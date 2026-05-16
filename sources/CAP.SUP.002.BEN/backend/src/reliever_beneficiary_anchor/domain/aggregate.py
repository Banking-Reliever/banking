"""AGG.SUP.002.BEN.IDENTITY_ANCHOR — the consistency boundary for one anchor.

This module is the canonical place where the invariants of the aggregate
are enforced. The application layer orchestrates persistence and outbox
writes around the aggregate, but it cannot reach inside the aggregate to
mutate state directly — every transition goes through a method here.

TASK-002 implements only the MINT transition. UPDATE / ARCHIVE / RESTORE /
PSEUDONYMISE land at TASK-003 … TASK-005.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from uuid_extensions import uuid7

from .errors import IdentityFieldsMissing
from .events import AnchorMinted
from .value_objects import (
    Actor,
    AnchorStatus,
    ClientRequestId,
    ContactDetails,
    InternalId,
    Pii,
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _mint_uuidv7() -> str:
    """RFC-9562 §5.7 UUIDv7. Wall-clock prefixed, k-sortable, version=7."""
    return str(uuid7())


@dataclass(slots=True)
class IdentityAnchor:
    """The aggregate root. Holds state + enforces invariants."""

    internal_id: InternalId
    pii: Pii
    anchor_status: AnchorStatus
    creation_date: date
    revision: int
    pseudonymized_at: datetime | None = None
    last_processed_command_id: str | None = None
    last_processed_client_request_id: str | None = None
    # Pending domain events buffered for the application layer to translate
    # into outbox rows. Cleared once persisted.
    _pending_events: list[AnchorMinted] = field(default_factory=list)

    # ─── Factory — MINT_ANCHOR ─────────────────────────────────────────

    @classmethod
    def mint(
        cls,
        *,
        client_request_id: ClientRequestId,
        last_name: str | None,
        first_name: str | None,
        date_of_birth: date | None,
        contact_details: ContactDetails | None,
        actor: Actor,
    ) -> "IdentityAnchor":
        """Mint a new anchor and buffer the MINTED domain event.

        Enforces:
          - INV.BEN.001 — server mints UUIDv7 (no caller-supplied id reaches here)
          - INV.BEN.007 — emits exactly one event carrying the full post-state
          - INV.BEN.008 — caller-side; idempotency is enforced at the application
            boundary against the idempotency_keys table.

        Raises ``IdentityFieldsMissing`` (PRE.002) if any required field is
        missing or empty.
        """
        # PRE.002 — required identity fields.
        missing: list[str] = []
        if not last_name:
            missing.append("last_name")
        if not first_name:
            missing.append("first_name")
        if date_of_birth is None:
            missing.append("date_of_birth")
        if missing:
            raise IdentityFieldsMissing(missing)

        # INV.BEN.001 — server mints. The aggregate is the only legitimate
        # source of internal_id. No caller-supplied id flows into this method.
        internal_id = InternalId(_mint_uuidv7())
        now = _now_utc()

        anchor = cls(
            internal_id=internal_id,
            pii=Pii(
                last_name=last_name,
                first_name=first_name,
                date_of_birth=date_of_birth,
                contact_details=contact_details,
            ),
            anchor_status="ACTIVE",
            creation_date=now.date(),
            revision=1,
            pseudonymized_at=None,
            last_processed_command_id=None,
            last_processed_client_request_id=str(client_request_id),
        )

        # INV.BEN.007 — emit ONE event per transition with the full snapshot.
        anchor._pending_events.append(
            AnchorMinted(
                internal_id=internal_id,
                last_name=last_name,  # type: ignore[arg-type] — guarded above
                first_name=first_name,  # type: ignore[arg-type]
                date_of_birth=date_of_birth,  # type: ignore[arg-type]
                contact_details=contact_details,
                creation_date=anchor.creation_date,
                revision=anchor.revision,
                transition_kind="MINTED",
                command_id=str(client_request_id),
                occurred_at=now,
                actor=actor,
            )
        )
        return anchor

    # ─── Pending events ────────────────────────────────────────────────

    def pull_pending_events(self) -> list[AnchorMinted]:
        events = list(self._pending_events)
        self._pending_events.clear()
        return events
