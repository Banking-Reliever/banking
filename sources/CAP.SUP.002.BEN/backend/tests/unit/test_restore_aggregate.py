"""Domain-layer unit tests for ``IdentityAnchor.restore`` — pure Python.

Covers INV.BEN.005 (ARCHIVED → ACTIVE), the round-trip ACTIVE → ARCHIVED
→ ACTIVE, illegal transitions, and the reason enum surface.
"""

from __future__ import annotations

from datetime import date

import pytest

from reliever_beneficiary_anchor.domain.aggregate import (
    RESTORE_REASONS,
    IdentityAnchor,
)
from reliever_beneficiary_anchor.domain.errors import (
    AnchorNotArchived,
    AnchorPseudonymised,
    InvalidReason,
)
from reliever_beneficiary_anchor.domain.events import AnchorRestored
from reliever_beneficiary_anchor.domain.value_objects import (
    Actor,
    ClientRequestId,
    ContactDetails,
)


def _crid() -> ClientRequestId:
    return ClientRequestId("018f8e10-1111-7000-8000-000000000001")


def _actor() -> Actor:
    return Actor(kind="human", subject="018f8e10-2222-7000-8000-000000000001")


def _command_id() -> str:
    return "018f8e10-3333-7000-8000-000000000010"


def _fresh_archived_anchor() -> IdentityAnchor:
    a = IdentityAnchor.mint(
        client_request_id=_crid(),
        last_name="Doe",
        first_name="Jane",
        date_of_birth=date(1990, 1, 15),
        contact_details=ContactDetails(email="jane@example.org"),
        actor=_actor(),
    )
    _ = a.pull_pending_events()
    a.archive(
        reason="PROGRAMME_EXIT_SUCCESS",
        command_id="018f8e10-3333-7000-8000-000000000099",
        actor=_actor(),
    )
    _ = a.pull_pending_events()
    return a


class TestRestoreTransition:
    def test_flips_archived_to_active(self):
        a = _fresh_archived_anchor()
        assert a.anchor_status == "ARCHIVED"
        a.restore(
            reason="ARCHIVED_IN_ERROR",
            command_id=_command_id(),
            actor=_actor(),
        )
        assert a.anchor_status == "ACTIVE"

    def test_revision_increments_by_one(self):
        a = _fresh_archived_anchor()
        rev_before = a.revision
        a.restore(
            reason="ARCHIVED_IN_ERROR",
            command_id=_command_id(),
            actor=_actor(),
        )
        assert a.revision == rev_before + 1

    def test_emits_exactly_one_restored_event(self):
        a = _fresh_archived_anchor()
        a.restore(
            reason="REINSTATED_AFTER_REVIEW",
            command_id=_command_id(),
            actor=_actor(),
            comment="Granted by DPO review board.",
        )
        events = a.pull_pending_events()
        assert len(events) == 1
        evt = events[0]
        assert isinstance(evt, AnchorRestored)
        assert evt.transition_kind == "RESTORED"
        assert evt.revision == a.revision
        assert evt.command_id == _command_id()
        assert evt.reason == "REINSTATED_AFTER_REVIEW"
        assert evt.comment == "Granted by DPO review board."

    def test_inv_ben_002_pii_unchanged_across_restore(self):
        a = _fresh_archived_anchor()
        pre_internal_id = a.internal_id.value
        pre_last_name = a.pii.last_name
        pre_first_name = a.pii.first_name
        pre_dob = a.pii.date_of_birth
        pre_contact = a.pii.contact_details

        a.restore(
            reason="ARCHIVED_IN_ERROR",
            command_id=_command_id(),
            actor=_actor(),
        )

        assert a.internal_id.value == pre_internal_id
        assert a.pii.last_name == pre_last_name
        assert a.pii.first_name == pre_first_name
        assert a.pii.date_of_birth == pre_dob
        assert a.pii.contact_details == pre_contact

    def test_restore_on_active_raises_not_archived(self):
        # Start with a freshly minted ACTIVE anchor (no prior archive).
        a = IdentityAnchor.mint(
            client_request_id=_crid(),
            last_name="Doe",
            first_name="Jane",
            date_of_birth=date(1990, 1, 15),
            contact_details=None,
            actor=_actor(),
        )
        _ = a.pull_pending_events()
        assert a.anchor_status == "ACTIVE"
        with pytest.raises(AnchorNotArchived) as exc:
            a.restore(
                reason="ARCHIVED_IN_ERROR",
                command_id=_command_id(),
                actor=_actor(),
            )
        assert exc.value.code == "ANCHOR_NOT_ARCHIVED"
        # No event was buffered for the rejected call.
        assert a.pull_pending_events() == []

    def test_restore_on_pseudonymised_raises_pseudonymised(self):
        a = _fresh_archived_anchor()
        a.anchor_status = "PSEUDONYMISED"
        with pytest.raises(AnchorPseudonymised) as exc:
            a.restore(
                reason="ARCHIVED_IN_ERROR",
                command_id=_command_id(),
                actor=_actor(),
            )
        assert exc.value.code == "ANCHOR_PSEUDONYMISED"

    @pytest.mark.parametrize(
        "bad_reason",
        [None, "", "not-a-canonical-reason", "archived_in_error", "INVALID"],
    )
    def test_invalid_reason_raises_invalid_reason(self, bad_reason):
        a = _fresh_archived_anchor()
        with pytest.raises(InvalidReason) as exc:
            a.restore(
                reason=bad_reason,  # type: ignore[arg-type]
                command_id=_command_id(),
                actor=_actor(),
            )
        assert exc.value.code == "INVALID_REASON"

    @pytest.mark.parametrize("good_reason", sorted(RESTORE_REASONS))
    def test_every_canonical_reason_accepted(self, good_reason):
        a = _fresh_archived_anchor()
        a.restore(
            reason=good_reason,
            command_id=_command_id(),
            actor=_actor(),
        )
        assert a.anchor_status == "ACTIVE"

    def test_round_trip_active_archived_active_revision_three(self):
        # Start at revision=1 (MINTED).
        a = IdentityAnchor.mint(
            client_request_id=_crid(),
            last_name="Doe",
            first_name="Jane",
            date_of_birth=date(1990, 1, 15),
            contact_details=None,
            actor=_actor(),
        )
        _ = a.pull_pending_events()
        assert a.revision == 1
        assert a.anchor_status == "ACTIVE"

        # ARCHIVE — revision=2.
        a.archive(
            reason="PROGRAMME_EXIT_SUCCESS",
            command_id="018f8e10-3333-7000-8000-000000000020",
            actor=_actor(),
        )
        _ = a.pull_pending_events()
        assert a.revision == 2
        assert a.anchor_status == "ARCHIVED"

        # RESTORE — revision=3, back to ACTIVE.
        a.restore(
            reason="ARCHIVED_IN_ERROR",
            command_id="018f8e10-3333-7000-8000-000000000021",
            actor=_actor(),
        )
        evts = a.pull_pending_events()
        assert a.revision == 3
        assert a.anchor_status == "ACTIVE"
        assert len(evts) == 1
        assert isinstance(evts[0], AnchorRestored)
