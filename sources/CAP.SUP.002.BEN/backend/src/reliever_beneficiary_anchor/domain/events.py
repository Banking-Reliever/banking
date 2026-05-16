"""Domain events emitted by the aggregate (in-process; not the wire RVT yet).

The application layer translates these into wire-format
``RVT.SUP.002.BENEFICIARY_ANCHOR_UPDATED`` payloads via the schema mapper
in ``infrastructure.messaging``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from .value_objects import (
    Actor,
    ContactDetails,
    InternalId,
    TransitionKind,
)


@dataclass(frozen=True, slots=True)
class AnchorMinted:
    """Emitted by AGG.IDENTITY_ANCHOR when MINT_ANCHOR is accepted.

    Carries the full post-transition snapshot — matches RVT semantics
    (INV.BEN.007: every accepted transition emits the full post-state).
    """

    internal_id: InternalId
    last_name: str
    first_name: str
    date_of_birth: date
    contact_details: ContactDetails | None
    creation_date: date
    revision: int
    transition_kind: TransitionKind  # always "MINTED" for this event
    command_id: str  # carries the client_request_id (per RVT schema)
    occurred_at: datetime
    actor: Actor
