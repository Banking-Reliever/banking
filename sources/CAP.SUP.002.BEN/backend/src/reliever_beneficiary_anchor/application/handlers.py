"""Use-case handlers — MintAnchorHandler and GetAnchorHandler.

The handlers are framework-agnostic; FastAPI invokes them from the
presentation routers via DI.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from uuid_extensions import uuid7

from ..domain.aggregate import IdentityAnchor
from ..domain.errors import AnchorNotFound, DomainError
from ..domain.events import AnchorMinted
from ..domain.value_objects import Actor, ClientRequestId
from .dto import BeneficiaryAnchorDto, MintAnchorCommandDto
from .ports import (
    AnchorDirectoryReader,
    SchemaValidator,
    UnitOfWorkFactory,
)

# Bus topology — derived verbatim from process/CAP.SUP.002.BEN/bus.yaml.
EXCHANGE_NAME = "sup.002.ben-events"
RVT_EVENT_NAME = "RVT.SUP.002.BENEFICIARY_ANCHOR_UPDATED"
BUSINESS_EVENT_NAME = "EVT.SUP.002.BENEFICIARY_ANCHOR_UPDATED"
ROUTING_KEY = f"{BUSINESS_EVENT_NAME}.{RVT_EVENT_NAME}"
SCHEMA_ID = "https://reliever.banking/process/CAP.SUP.002.BEN/schemas/RVT.SUP.002.BENEFICIARY_ANCHOR_UPDATED.schema.json"
SCHEMA_VERSION = "0.1.0"
EMITTING_CAPABILITY = "CAP.SUP.002.BEN"


@dataclass(frozen=True, slots=True)
class MintResult:
    """Result of CMD.MINT_ANCHOR. ``http_status`` is 201 for a fresh mint and
    200 for an idempotent re-call (REQUEST_ALREADY_PROCESSED).
    """

    anchor: BeneficiaryAnchorDto
    http_status: int
    idempotent_replay: bool
    error_code: str | None = None


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _mint_uuidv7() -> str:
    return str(uuid7())


def _build_rvt_payload(event: AnchorMinted, actor: Actor) -> dict[str, Any]:
    """Translate a domain ``AnchorMinted`` event into the wire-format
    ``RVT.SUP.002.BENEFICIARY_ANCHOR_UPDATED`` payload.

    Validated against the canonical JSON Schema before the outbox row is
    written (fail-fast on contract drift).
    """
    payload: dict[str, Any] = {
        "envelope": {
            "message_id": _mint_uuidv7(),
            "schema_version": SCHEMA_VERSION,
            "emitted_at": _now_utc().isoformat(),
            "emitting_capability": EMITTING_CAPABILITY,
            "correlation_id": str(event.internal_id),  # anchor-scoped correlation
            "causation_id": event.command_id,
            "actor": actor.to_dict(),
        },
        "internal_id": str(event.internal_id),
        "last_name": event.last_name,
        "first_name": event.first_name,
        "date_of_birth": event.date_of_birth.isoformat(),
        "contact_details": event.contact_details.to_dict() if event.contact_details else None,
        "anchor_status": "ACTIVE",
        "creation_date": event.creation_date.isoformat(),
        "pseudonymized_at": None,
        "revision": event.revision,
        "transition_kind": event.transition_kind,
        "command_id": event.command_id,
        "right_exercise_id": None,
        "occurred_at": event.occurred_at.isoformat(),
    }
    return payload


class MintAnchorHandler:
    def __init__(
        self,
        *,
        uow_factory: UnitOfWorkFactory,
        rvt_validator: SchemaValidator,
    ) -> None:
        self._uow_factory = uow_factory
        self._rvt_validator = rvt_validator

    async def handle(self, cmd: MintAnchorCommandDto) -> MintResult:
        scope = "MINT_ANCHOR"

        # ─── Idempotency check (INV.BEN.008) ──────────────────────────
        async with self._uow_factory() as uow:
            prior = await uow.idempotency.get(scope=scope, key=cmd.client_request_id)
            if prior is not None:
                # Idempotent replay — return the original anchor.
                stored: dict[str, Any] = prior["response_body"]
                return MintResult(
                    anchor=_deserialize_anchor(stored),
                    http_status=200,
                    idempotent_replay=True,
                    error_code="REQUEST_ALREADY_PROCESSED",
                )

        # ─── Fresh mint ───────────────────────────────────────────────
        async with self._uow_factory() as uow:
            # Re-check inside the transaction — defends against the very
            # narrow race where two POSTs arrive simultaneously with the
            # same client_request_id.
            prior = await uow.idempotency.get(scope=scope, key=cmd.client_request_id)
            if prior is not None:
                stored = prior["response_body"]
                await uow.rollback()
                return MintResult(
                    anchor=_deserialize_anchor(stored),
                    http_status=200,
                    idempotent_replay=True,
                    error_code="REQUEST_ALREADY_PROCESSED",
                )

            anchor = IdentityAnchor.mint(
                client_request_id=ClientRequestId(cmd.client_request_id),
                last_name=cmd.last_name,
                first_name=cmd.first_name,
                date_of_birth=cmd.date_of_birth,
                contact_details=cmd.contact_details,
                actor=cmd.actor,
            )
            # IdentityAnchor.mint() raises IdentityFieldsMissing on PRE.002.

            await uow.anchors.insert(anchor)

            events = anchor.pull_pending_events()
            assert len(events) == 1, "AGG must emit exactly one event per transition (INV.BEN.007)"
            event = events[0]

            # Validate the wire-format payload BEFORE writing the outbox row.
            payload = _build_rvt_payload(event, cmd.actor)
            self._rvt_validator.validate_payload(payload)

            message_id = payload["envelope"]["message_id"]
            await uow.outbox.append(
                message_id=message_id,
                correlation_id=str(event.internal_id),
                causation_id=event.command_id,
                schema_id=SCHEMA_ID,
                schema_version=SCHEMA_VERSION,
                routing_key=ROUTING_KEY,
                exchange=EXCHANGE_NAME,
                occurred_at=event.occurred_at,
                actor=cmd.actor.to_dict(),
                payload=payload,
            )

            # Idempotency record — must be in the same transaction so the
            # row is durable iff the anchor row is.
            dto = BeneficiaryAnchorDto(
                internal_id=str(anchor.internal_id),
                last_name=anchor.pii.last_name,
                first_name=anchor.pii.first_name,
                date_of_birth=anchor.pii.date_of_birth,
                contact_details=(anchor.pii.contact_details.to_dict()
                                 if anchor.pii.contact_details else None),
                anchor_status=anchor.anchor_status,
                creation_date=anchor.creation_date,
                pseudonymized_at=anchor.pseudonymized_at,
                revision=anchor.revision,
            )
            await uow.idempotency.remember(
                scope=scope,
                key=cmd.client_request_id,
                internal_id=str(anchor.internal_id),
                response_body=dto.to_dict(),
                response_code=201,
            )

            await uow.commit()
            return MintResult(anchor=dto, http_status=201, idempotent_replay=False)


def _deserialize_anchor(stored: dict[str, Any]) -> BeneficiaryAnchorDto:
    """Reconstruct a BeneficiaryAnchorDto from a stored idempotency response."""
    from datetime import date as _date

    creation_date = _date.fromisoformat(stored["creation_date"]) if stored.get("creation_date") else None
    date_of_birth = _date.fromisoformat(stored["date_of_birth"]) if stored.get("date_of_birth") else None
    pseudonymized_at = (
        datetime.fromisoformat(stored["pseudonymized_at"])
        if stored.get("pseudonymized_at")
        else None
    )
    assert creation_date is not None, "creation_date is required in stored payload"
    return BeneficiaryAnchorDto(
        internal_id=stored["internal_id"],
        last_name=stored.get("last_name"),
        first_name=stored.get("first_name"),
        date_of_birth=date_of_birth,
        contact_details=stored.get("contact_details"),
        anchor_status=stored["anchor_status"],
        creation_date=creation_date,
        pseudonymized_at=pseudonymized_at,
        revision=stored["revision"],
    )


class GetAnchorHandler:
    def __init__(self, *, reader: AnchorDirectoryReader) -> None:
        self._reader = reader

    async def handle(self, internal_id: str) -> BeneficiaryAnchorDto:
        # Defensive — the presentation layer will already have validated the
        # UUIDv7 format. Reject obviously malformed ids here too.
        try:
            uuid.UUID(internal_id)
        except ValueError as exc:
            raise AnchorNotFound(internal_id) from exc

        row = await self._reader.get(internal_id)
        if row is None:
            raise AnchorNotFound(internal_id)
        return _row_to_dto(row)


def _row_to_dto(row: dict[str, Any]) -> BeneficiaryAnchorDto:
    cd = row.get("contact_details")
    if isinstance(cd, str):
        cd = json.loads(cd)
    return BeneficiaryAnchorDto(
        internal_id=str(row["internal_id"]),
        last_name=row.get("last_name"),
        first_name=row.get("first_name"),
        date_of_birth=row.get("date_of_birth"),
        contact_details=cd,
        anchor_status=row["anchor_status"],
        creation_date=row["creation_date"],
        pseudonymized_at=row.get("pseudonymized_at"),
        revision=row["revision"],
    )


__all__ = [
    "MintAnchorHandler",
    "GetAnchorHandler",
    "MintResult",
    "EXCHANGE_NAME",
    "ROUTING_KEY",
    "SCHEMA_ID",
    "SCHEMA_VERSION",
    "EMITTING_CAPABILITY",
]
