"""AGG.SUP.002.BEN.IDENTITY_ANCHOR — the consistency boundary for one anchor.

This module is the canonical place where the invariants of the aggregate
are enforced. The application layer orchestrates persistence and outbox
writes around the aggregate, but it cannot reach inside the aggregate to
mutate state directly — every transition goes through a method here.

TASK-002 implements MINT. TASK-004 adds ARCHIVE / RESTORE. UPDATE lands at
TASK-003 (parallel branch). PSEUDONYMISE lands at TASK-005.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Union

from uuid_extensions import uuid7

from .errors import (
    AnchorAlreadyArchived,
    AnchorNotArchived,
    AnchorPseudonymised,
    IdentityFieldsMissing,
    InvalidReason,
)
from .events import AnchorArchived, AnchorMinted, AnchorRestored
from .value_objects import (
    Actor,
    AnchorStatus,
    ClientRequestId,
    ContactDetails,
    InternalId,
    Pii,
)

# Canonical archive reasons — mirror process/.../CMD.ARCHIVE_ANCHOR.schema.json.
ARCHIVE_REASONS: frozenset[str] = frozenset(
    {
        "PROGRAMME_EXIT_SUCCESS",
        "PROGRAMME_EXIT_DROPOUT",
        "PROGRAMME_EXIT_TRANSFER",
        "ADMINISTRATIVE_ARCHIVAL",
    }
)

# Canonical restore reasons — mirror process/.../CMD.RESTORE_ANCHOR.schema.json.
RESTORE_REASONS: frozenset[str] = frozenset(
    {"ARCHIVED_IN_ERROR", "REINSTATED_AFTER_REVIEW"}
)

# Union of every domain event the aggregate may emit. ``pull_pending_events``
# returns ``list[PendingEvent]`` to give the application layer a single,
# discriminated-union return type.
PendingEvent = Union[AnchorMinted, AnchorArchived, AnchorRestored]


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
    _pending_events: list[PendingEvent] = field(default_factory=list)

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

    # ─── Transition — ARCHIVE_ANCHOR ───────────────────────────────────

    def archive(
        self,
        *,
        reason: str,
        command_id: str,
        actor: Actor,
        comment: str | None = None,
    ) -> None:
        """Flip ACTIVE → ARCHIVED (INV.BEN.004) and buffer the ARCHIVED event.

        Refuses (raises ``AnchorAlreadyArchived``) if the anchor is already
        ARCHIVED, and (``AnchorPseudonymised``) if the anchor is in the
        terminal PSEUDONYMISED state. PII fields are NOT mutated
        (INV.BEN.002 — internal_id and PII immutable across ARCHIVE).
        """
        if self.anchor_status == "PSEUDONYMISED":
            raise AnchorPseudonymised(str(self.internal_id))
        if self.anchor_status == "ARCHIVED":
            raise AnchorAlreadyArchived(str(self.internal_id))
        if reason not in ARCHIVE_REASONS:
            raise InvalidReason("ARCHIVE_ANCHOR", reason)

        # State transition. PII and creation_date are sticky (INV.BEN.002).
        self.anchor_status = "ARCHIVED"
        self.revision += 1
        self.last_processed_command_id = command_id

        self._pending_events.append(
            AnchorArchived(
                internal_id=self.internal_id,
                last_name=self.pii.last_name,
                first_name=self.pii.first_name,
                date_of_birth=self.pii.date_of_birth,
                contact_details=self.pii.contact_details,
                creation_date=self.creation_date,
                revision=self.revision,
                transition_kind="ARCHIVED",
                command_id=command_id,
                occurred_at=_now_utc(),
                actor=actor,
                reason=reason,
                comment=comment,
            )
        )

    # ─── Transition — RESTORE_ANCHOR ───────────────────────────────────

    def restore(
        self,
        *,
        reason: str,
        command_id: str,
        actor: Actor,
        comment: str | None = None,
    ) -> None:
        """Flip ARCHIVED → ACTIVE (INV.BEN.005) and buffer the RESTORED event.

        Refuses (raises ``AnchorNotArchived``) if the anchor is ACTIVE, and
        (``AnchorPseudonymised``) if it is PSEUDONYMISED. PII fields are NOT
        mutated.
        """
        if self.anchor_status == "PSEUDONYMISED":
            raise AnchorPseudonymised(str(self.internal_id))
        if self.anchor_status != "ARCHIVED":
            raise AnchorNotArchived(str(self.internal_id))
        if reason not in RESTORE_REASONS:
            raise InvalidReason("RESTORE_ANCHOR", reason)

        self.anchor_status = "ACTIVE"
        self.revision += 1
        self.last_processed_command_id = command_id

        self._pending_events.append(
            AnchorRestored(
                internal_id=self.internal_id,
                last_name=self.pii.last_name,
                first_name=self.pii.first_name,
                date_of_birth=self.pii.date_of_birth,
                contact_details=self.pii.contact_details,
                creation_date=self.creation_date,
                revision=self.revision,
                transition_kind="RESTORED",
                command_id=command_id,
                occurred_at=_now_utc(),
                actor=actor,
                reason=reason,
                comment=comment,
            )
        )

    # ─── Pending events ────────────────────────────────────────────────

    def pull_pending_events(self) -> list[PendingEvent]:
        events = list(self._pending_events)
        self._pending_events.clear()
        return events
