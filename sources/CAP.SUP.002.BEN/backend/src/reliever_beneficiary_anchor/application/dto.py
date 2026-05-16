"""DTOs crossing the application boundary.

These are *internal* — the presentation layer maps them to JSON; the schema
validator works on dicts. The wire-format BeneficiaryAnchor is what the
HTTP responses serialise.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from ..domain.value_objects import Actor, ContactDetails


@dataclass(frozen=True, slots=True)
class MintAnchorCommandDto:
    """Input payload of CMD.MINT_ANCHOR — already passed through JSON Schema
    validation at the presentation boundary.

    Note: ``internal_id`` is intentionally absent from the command DTO —
    the server mints it (INV.BEN.001). The presentation layer rejects any
    request body that carries one.
    """

    client_request_id: str
    last_name: str
    first_name: str
    date_of_birth: date
    contact_details: ContactDetails | None
    actor: Actor


@dataclass(frozen=True, slots=True)
class ArchiveAnchorCommandDto:
    """Input payload of CMD.ARCHIVE_ANCHOR — already validated against
    the canonical schema at the presentation boundary.
    """

    internal_id: str
    command_id: str
    reason: str  # one of ARCHIVE_REASONS in the aggregate
    actor: Actor
    comment: str | None = None


@dataclass(frozen=True, slots=True)
class RestoreAnchorCommandDto:
    """Input payload of CMD.RESTORE_ANCHOR — already validated against
    the canonical schema at the presentation boundary.
    """

    internal_id: str
    command_id: str
    reason: str  # one of RESTORE_REASONS in the aggregate
    actor: Actor
    comment: str | None = None


@dataclass(frozen=True, slots=True)
class BeneficiaryAnchorDto:
    """Canonical wire-format BeneficiaryAnchor — matches the QRY.GET_ANCHOR
    response and the 201 response of POST /anchors.

    The pseudonymised branch returns the four PII fields as None.
    """

    internal_id: str
    last_name: str | None
    first_name: str | None
    date_of_birth: date | None
    contact_details: dict[str, Any] | None
    anchor_status: str
    creation_date: date
    pseudonymized_at: datetime | None
    revision: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "internal_id": self.internal_id,
            "last_name": self.last_name,
            "first_name": self.first_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "contact_details": self.contact_details,
            "anchor_status": self.anchor_status,
            "creation_date": self.creation_date.isoformat(),
            "pseudonymized_at": self.pseudonymized_at.isoformat() if self.pseudonymized_at else None,
            "revision": self.revision,
        }
