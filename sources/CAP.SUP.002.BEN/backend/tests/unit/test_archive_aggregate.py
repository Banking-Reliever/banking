"""Domain-layer unit tests for ``IdentityAnchor.archive`` — pure Python.

Covers INV.BEN.002 (snapshot continuity), INV.BEN.004 (ACTIVE → ARCHIVED),
INV.BEN.007 (one event per transition with full snapshot), the
PSEUDONYMISED terminal-state guard (INV.BEN.007), and the reason-enum
validation surface.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from reliever_beneficiary_anchor.domain.aggregate import (
    ARCHIVE_REASONS,
    IdentityAnchor,
)
from reliever_beneficiary_anchor.domain.errors import (
    AnchorAlreadyArchived,
    AnchorPseudonymised,
    InvalidReason,
)
from reliever_beneficiary_anchor.domain.events import AnchorArchived
from reliever_beneficiary_anchor.domain.value_objects import (
    Actor,
    ClientRequestId,
    ContactDetails,
    InternalId,
    Pii,
)


def _crid() -> ClientRequestId:
    return ClientRequestId("018f8e10-1111-7000-8000-000000000001")


def _actor() -> Actor:
    return Actor(kind="human", subject="018f8e10-2222-7000-8000-000000000001")


def _command_id() -> str:
    return "018f8e10-3333-7000-8000-000000000001"


def _fresh_active_anchor() -> IdentityAnchor:
    """Mint a fresh ACTIVE anchor for use as a test fixture and clear the
    pending MINTED event so each test starts from a clean buffer."""
    a = IdentityAnchor.mint(
        client_request_id=_crid(),
        last_name="Doe",
        first_name="Jane",
        date_of_birth=date(1990, 1, 15),
        contact_details=ContactDetails(email="jane@example.org"),
        actor=_actor(),
    )
    _ = a.pull_pending_events()  # drain the MINTED event
    return a


class TestArchiveTransition:
    def test_flips_active_to_archived(self):
        a = _fresh_active_anchor()
        assert a.anchor_status == "ACTIVE"
        a.archive(
            reason="PROGRAMME_EXIT_SUCCESS",
            command_id=_command_id(),
            actor=_actor(),
        )
        assert a.anchor_status == "ARCHIVED"

    def test_revision_increments_by_one(self):
        a = _fresh_active_anchor()
        rev_before = a.revision
        a.archive(
            reason="PROGRAMME_EXIT_SUCCESS",
            command_id=_command_id(),
            actor=_actor(),
        )
        assert a.revision == rev_before + 1

    def test_emits_exactly_one_archived_event(self):
        a = _fresh_active_anchor()
        a.archive(
            reason="PROGRAMME_EXIT_DROPOUT",
            command_id=_command_id(),
            actor=_actor(),
            comment="Beneficiary withdrew from programme.",
        )
        events = a.pull_pending_events()
        assert len(events) == 1
        evt = events[0]
        assert isinstance(evt, AnchorArchived)
        assert evt.transition_kind == "ARCHIVED"
        assert evt.revision == a.revision
        assert evt.command_id == _command_id()
        assert evt.reason == "PROGRAMME_EXIT_DROPOUT"
        assert evt.comment == "Beneficiary withdrew from programme."

    def test_inv_ben_002_pii_unchanged_across_archive(self):
        a = _fresh_active_anchor()
        pre_internal_id = a.internal_id.value
        pre_last_name = a.pii.last_name
        pre_first_name = a.pii.first_name
        pre_dob = a.pii.date_of_birth
        pre_contact = a.pii.contact_details

        a.archive(
            reason="ADMINISTRATIVE_ARCHIVAL",
            command_id=_command_id(),
            actor=_actor(),
        )

        # internal_id is the linchpin of INV.BEN.002.
        assert a.internal_id.value == pre_internal_id
        # PII fields are sticky across ARCHIVE.
        assert a.pii.last_name == pre_last_name
        assert a.pii.first_name == pre_first_name
        assert a.pii.date_of_birth == pre_dob
        assert a.pii.contact_details == pre_contact

    def test_event_carries_full_post_state_snapshot(self):
        a = _fresh_active_anchor()
        a.archive(
            reason="PROGRAMME_EXIT_TRANSFER",
            command_id=_command_id(),
            actor=_actor(),
        )
        evt = a.pull_pending_events()[0]
        assert isinstance(evt, AnchorArchived)
        assert evt.last_name == a.pii.last_name
        assert evt.first_name == a.pii.first_name
        assert evt.date_of_birth == a.pii.date_of_birth
        assert evt.contact_details == a.pii.contact_details
        assert evt.creation_date == a.creation_date
        assert isinstance(evt.occurred_at, datetime)
        assert evt.occurred_at.tzinfo == timezone.utc

    def test_archive_twice_raises_already_archived(self):
        a = _fresh_active_anchor()
        a.archive(
            reason="PROGRAMME_EXIT_SUCCESS",
            command_id=_command_id(),
            actor=_actor(),
        )
        _ = a.pull_pending_events()  # drain
        with pytest.raises(AnchorAlreadyArchived) as exc:
            a.archive(
                reason="PROGRAMME_EXIT_SUCCESS",
                command_id="018f8e10-3333-7000-8000-000000000002",
                actor=_actor(),
            )
        assert exc.value.code == "ANCHOR_ALREADY_ARCHIVED"
        # No new event was buffered for the rejected call.
        assert a.pull_pending_events() == []

    def test_archive_on_pseudonymised_raises_pseudonymised(self):
        a = _fresh_active_anchor()
        # Simulate a PSEUDONYMISED state without going through that command —
        # TASK-005 lands the real path. The transition flag is what matters.
        a.anchor_status = "PSEUDONYMISED"
        with pytest.raises(AnchorPseudonymised) as exc:
            a.archive(
                reason="PROGRAMME_EXIT_SUCCESS",
                command_id=_command_id(),
                actor=_actor(),
            )
        assert exc.value.code == "ANCHOR_PSEUDONYMISED"

    @pytest.mark.parametrize(
        "bad_reason",
        [
            None,
            "",
            "not-a-canonical-reason",
            "programme_exit_success",  # case-sensitive
            "INVALID",
        ],
    )
    def test_invalid_reason_raises_invalid_reason(self, bad_reason):
        a = _fresh_active_anchor()
        with pytest.raises(InvalidReason) as exc:
            a.archive(
                reason=bad_reason,  # type: ignore[arg-type]
                command_id=_command_id(),
                actor=_actor(),
            )
        assert exc.value.code == "INVALID_REASON"

    @pytest.mark.parametrize("good_reason", sorted(ARCHIVE_REASONS))
    def test_every_canonical_reason_accepted(self, good_reason):
        a = _fresh_active_anchor()
        a.archive(
            reason=good_reason,
            command_id=_command_id(),
            actor=_actor(),
        )
        assert a.anchor_status == "ARCHIVED"

    def test_archive_updates_last_processed_command_id(self):
        a = _fresh_active_anchor()
        a.archive(
            reason="PROGRAMME_EXIT_SUCCESS",
            command_id=_command_id(),
            actor=_actor(),
        )
        assert a.last_processed_command_id == _command_id()
