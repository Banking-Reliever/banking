"""AGG.SUP.002.BEN.IDENTITY_ANCHOR consistency boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING

from uuid_extensions import uuid7

from .errors import (
    AnchorAlreadyArchived,
    AnchorArchived,
    AnchorNotArchived,
    AnchorPseudonymised,
    IdentityFieldsMissing,
    InternalIdImmutable,
    InvalidReason,
    NoFieldsToUpdate,
)
from .events import AnchorArchived as AnchorArchivedEvent
from .events import AnchorMinted, AnchorRestored, AnchorUpdated, TransitionEvent
from .value_objects import (
    Actor,
    AnchorStatus,
    ClientRequestId,
    ContactDetails,
    InternalId,
    Pii,
)

if TYPE_CHECKING:  # pragma: no cover
    from ..application.dto import UpdateFields

ARCHIVE_REASONS: frozenset[str] = frozenset(
    {
        "PROGRAMME_EXIT_SUCCESS",
        "PROGRAMME_EXIT_DROPOUT",
        "PROGRAMME_EXIT_TRANSFER",
        "ADMINISTRATIVE_ARCHIVAL",
    }
)
RESTORE_REASONS: frozenset[str] = frozenset({"ARCHIVED_IN_ERROR", "REINSTATED_AFTER_REVIEW"})


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _mint_uuidv7() -> str:
    return str(uuid7())


@dataclass(slots=True)
class IdentityAnchor:
    internal_id: InternalId
    pii: Pii
    anchor_status: AnchorStatus
    creation_date: date
    revision: int
    pseudonymized_at: datetime | None = None
    last_processed_command_id: str | None = None
    last_processed_client_request_id: str | None = None
    _pending_events: list[TransitionEvent] = field(default_factory=list)

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
        missing: list[str] = []
        if not last_name:
            missing.append("last_name")
        if not first_name:
            missing.append("first_name")
        if date_of_birth is None:
            missing.append("date_of_birth")
        if missing:
            raise IdentityFieldsMissing(missing)

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
        anchor._pending_events.append(
            AnchorMinted(
                internal_id=internal_id,
                last_name=last_name,
                first_name=first_name,
                date_of_birth=date_of_birth,
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

    @classmethod
    def hydrate(
        cls,
        *,
        internal_id: str,
        last_name: str | None,
        first_name: str | None,
        date_of_birth: date | None,
        contact_details: ContactDetails | None,
        anchor_status: AnchorStatus,
        creation_date: date,
        revision: int,
        pseudonymized_at: datetime | None = None,
        last_processed_command_id: str | None = None,
        last_processed_client_request_id: str | None = None,
    ) -> "IdentityAnchor":
        return cls(
            internal_id=InternalId(internal_id),
            pii=Pii(
                last_name=last_name,
                first_name=first_name,
                date_of_birth=date_of_birth,
                contact_details=contact_details,
            ),
            anchor_status=anchor_status,
            creation_date=creation_date,
            revision=revision,
            pseudonymized_at=pseudonymized_at,
            last_processed_command_id=last_processed_command_id,
            last_processed_client_request_id=last_processed_client_request_id,
        )

    def update(self, *, command_id: str, fields: "UpdateFields", actor: Actor) -> None:
        if self.anchor_status == "ARCHIVED":
            raise AnchorArchived(str(self.internal_id))
        if self.anchor_status == "PSEUDONYMISED":
            raise AnchorPseudonymised(str(self.internal_id))
        assert self.anchor_status == "ACTIVE"

        if fields.attempts_internal_id_mutation:
            raise InternalIdImmutable()
        if not fields.has_any_mutation:
            raise NoFieldsToUpdate()

        new_last_name = fields.merge_last_name(self.pii.last_name)
        new_first_name = fields.merge_first_name(self.pii.first_name)
        new_dob = fields.merge_date_of_birth(self.pii.date_of_birth)
        new_contact = fields.merge_contact_details(self.pii.contact_details)

        assert new_last_name is not None
        assert new_first_name is not None
        assert new_dob is not None

        now = _now_utc()
        self.pii = Pii(
            last_name=new_last_name,
            first_name=new_first_name,
            date_of_birth=new_dob,
            contact_details=new_contact,
        )
        self.revision += 1
        self.last_processed_command_id = command_id
        self._pending_events.append(
            AnchorUpdated(
                internal_id=self.internal_id,
                last_name=new_last_name,
                first_name=new_first_name,
                date_of_birth=new_dob,
                contact_details=new_contact,
                creation_date=self.creation_date,
                revision=self.revision,
                transition_kind="UPDATED",
                command_id=command_id,
                occurred_at=now,
                actor=actor,
            )
        )

    def archive(
        self,
        *,
        reason: str,
        command_id: str,
        actor: Actor,
        comment: str | None = None,
    ) -> None:
        if self.anchor_status == "PSEUDONYMISED":
            raise AnchorPseudonymised(str(self.internal_id))
        if self.anchor_status == "ARCHIVED":
            raise AnchorAlreadyArchived(str(self.internal_id))
        if reason not in ARCHIVE_REASONS:
            raise InvalidReason("ARCHIVE_ANCHOR", reason)

        self.anchor_status = "ARCHIVED"
        self.revision += 1
        self.last_processed_command_id = command_id
        self._pending_events.append(
            AnchorArchivedEvent(
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

    def restore(
        self,
        *,
        reason: str,
        command_id: str,
        actor: Actor,
        comment: str | None = None,
    ) -> None:
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

    def pull_pending_events(self) -> list[TransitionEvent]:
        events = list(self._pending_events)
        self._pending_events.clear()
        return events


__all__ = ["IdentityAnchor", "ARCHIVE_REASONS", "RESTORE_REASONS"]
