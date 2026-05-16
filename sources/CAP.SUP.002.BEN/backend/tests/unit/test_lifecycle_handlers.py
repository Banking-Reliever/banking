"""Application-layer tests for ArchiveAnchorHandler / RestoreAnchorHandler.

In-memory ports — runs without Postgres or Rabbit. Asserts the full DoD
contract: idempotency, single-tx outbox + idempotency, RVT payload validates
against the canonical schema, snapshot continuity, error mapping.
"""

from __future__ import annotations

import copy
from datetime import date, datetime
from typing import Any

import pytest

from reliever_beneficiary_anchor.application.dto import (
    ArchiveAnchorCommandDto,
    MintAnchorCommandDto,
    RestoreAnchorCommandDto,
)
from reliever_beneficiary_anchor.application.handlers import (
    IDEMPOTENCY_SCOPE_ARCHIVE,
    IDEMPOTENCY_SCOPE_MINT,
    IDEMPOTENCY_SCOPE_RESTORE,
    ArchiveAnchorHandler,
    MintAnchorHandler,
    RestoreAnchorHandler,
)
from reliever_beneficiary_anchor.application.ports import (
    AnchorRepository,
    IdempotencyRepository,
    OutboxRepository,
    UnitOfWork,
    UnitOfWorkFactory,
)
from reliever_beneficiary_anchor.domain.aggregate import IdentityAnchor
from reliever_beneficiary_anchor.domain.errors import (
    AnchorAlreadyArchived,
    AnchorNotArchived,
    AnchorNotFound,
    AnchorPseudonymised,
)
from reliever_beneficiary_anchor.domain.value_objects import (
    Actor,
    ContactDetails,
)
from reliever_beneficiary_anchor.infrastructure.schema_validation.loader import (
    build_validators_bundle,
)


# ─── In-memory ports ───────────────────────────────────────────────────


class _InMemoryAnchorRepo(AnchorRepository):
    def __init__(self) -> None:
        # internal_id -> anchor instance (the SAME instance, so mutation
        # by ``get`` is observable in the test factory).
        self.rows: dict[str, IdentityAnchor] = {}

    async def insert(self, anchor: IdentityAnchor) -> None:
        self.rows[str(anchor.internal_id)] = anchor

    async def get(self, internal_id: str) -> IdentityAnchor | None:
        return self.rows.get(internal_id)

    async def update(self, anchor: IdentityAnchor) -> None:
        # The in-memory port mutates the stored aggregate in place, so
        # update() is effectively a no-op — but we still record the call.
        self.rows[str(anchor.internal_id)] = anchor


class _InMemoryOutboxRepo(OutboxRepository):
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    async def append(
        self,
        *,
        message_id: str,
        correlation_id: str,
        causation_id: str | None,
        schema_id: str,
        schema_version: str,
        routing_key: str,
        exchange: str,
        occurred_at: datetime,
        actor: dict[str, Any],
        payload: dict[str, Any],
    ) -> None:
        self.rows.append(
            {
                "message_id": message_id,
                "correlation_id": correlation_id,
                "causation_id": causation_id,
                "schema_id": schema_id,
                "schema_version": schema_version,
                "routing_key": routing_key,
                "exchange": exchange,
                "occurred_at": occurred_at,
                "actor": actor,
                "payload": payload,
            }
        )


class _InMemoryIdempotencyRepo(IdempotencyRepository):
    def __init__(self) -> None:
        self.rows: dict[tuple[str, str], dict[str, Any]] = {}

    async def get(self, scope: str, key: str) -> dict[str, Any] | None:
        return self.rows.get((scope, key))

    async def remember(
        self,
        *,
        scope: str,
        key: str,
        internal_id: str,
        response_body: dict[str, Any],
        response_code: int,
    ) -> None:
        self.rows.setdefault(
            (scope, key),
            {
                "scope": scope,
                "key": key,
                "internal_id": internal_id,
                "response_body": copy.deepcopy(response_body),
                "response_code": response_code,
            },
        )


class _InMemoryUoW(UnitOfWork):
    def __init__(self, anchors, outbox, idem):
        self.anchors = anchors
        self.outbox = outbox
        self.idempotency = idem
        self.committed = False
        self.rolled_back = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.rolled_back = True


class _InMemoryUoWFactory(UnitOfWorkFactory):
    def __init__(self):
        self.anchors = _InMemoryAnchorRepo()
        self.outbox = _InMemoryOutboxRepo()
        self.idem = _InMemoryIdempotencyRepo()
        self.uows: list[_InMemoryUoW] = []

    def __call__(self) -> _InMemoryUoW:
        u = _InMemoryUoW(self.anchors, self.outbox, self.idem)
        self.uows.append(u)
        return u


# ─── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def validators(schemas_dir):
    return build_validators_bundle(schemas_dir)


@pytest.fixture
def factory():
    return _InMemoryUoWFactory()


@pytest.fixture
def mint_handler(factory, validators):
    return MintAnchorHandler(uow_factory=factory, rvt_validator=validators.rvt)


@pytest.fixture
def archive_handler(factory, validators):
    return ArchiveAnchorHandler(
        uow_factory=factory, rvt_validator=validators.rvt
    )


@pytest.fixture
def restore_handler(factory, validators):
    return RestoreAnchorHandler(
        uow_factory=factory, rvt_validator=validators.rvt
    )


def _actor() -> Actor:
    return Actor(kind="human", subject="018f8e10-2222-7000-8000-000000000001")


def _mint_cmd(crid: str = "018f8e10-aaaa-7000-8000-000000000001") -> MintAnchorCommandDto:
    return MintAnchorCommandDto(
        client_request_id=crid,
        last_name="Dupont",
        first_name="Marie",
        date_of_birth=date(1985, 6, 21),
        contact_details=ContactDetails(email="marie.dupont@example.org"),
        actor=_actor(),
    )


async def _mint(handler: MintAnchorHandler, crid: str | None = None) -> str:
    cmd = _mint_cmd(crid or "018f8e10-aaaa-7000-8000-000000000001")
    result = await handler.handle(cmd)
    return result.anchor.internal_id


def _archive_cmd(internal_id: str, *, command_id: str, reason: str = "PROGRAMME_EXIT_SUCCESS") -> ArchiveAnchorCommandDto:
    return ArchiveAnchorCommandDto(
        internal_id=internal_id,
        command_id=command_id,
        reason=reason,
        actor=_actor(),
    )


def _restore_cmd(internal_id: str, *, command_id: str, reason: str = "ARCHIVED_IN_ERROR") -> RestoreAnchorCommandDto:
    return RestoreAnchorCommandDto(
        internal_id=internal_id,
        command_id=command_id,
        reason=reason,
        actor=_actor(),
    )


# ─── Archive handler tests ─────────────────────────────────────────────


class TestArchiveHandler:
    async def test_first_call_returns_200_and_flips_status(
        self, mint_handler, archive_handler, factory
    ):
        internal_id = await _mint(mint_handler)
        cmd = _archive_cmd(internal_id, command_id="018f8e10-bbbb-7000-8000-000000000001")
        result = await archive_handler.handle(cmd)

        assert result.http_status == 200
        assert result.idempotent_replay is False
        assert result.anchor.anchor_status == "ARCHIVED"
        assert result.anchor.revision == 2
        # In-memory aggregate observable in the repo.
        assert factory.anchors.rows[internal_id].anchor_status == "ARCHIVED"
        assert factory.anchors.rows[internal_id].revision == 2

    async def test_outbox_row_count_one_after_archive(
        self, mint_handler, archive_handler, factory
    ):
        internal_id = await _mint(mint_handler)
        # 1 outbox row from MINT.
        assert len(factory.outbox.rows) == 1
        cmd = _archive_cmd(internal_id, command_id="018f8e10-bbbb-7000-8000-000000000001")
        await archive_handler.handle(cmd)
        # Exactly one new outbox row for ARCHIVE.
        assert len(factory.outbox.rows) == 2

    async def test_outbox_carries_archived_transition_and_routing_key(
        self, mint_handler, archive_handler, factory, validators
    ):
        internal_id = await _mint(mint_handler)
        cmd = _archive_cmd(internal_id, command_id="018f8e10-bbbb-7000-8000-000000000001")
        await archive_handler.handle(cmd)
        row = factory.outbox.rows[-1]
        assert row["exchange"] == "sup.002.ben-events"
        assert row["routing_key"] == (
            "EVT.SUP.002.BENEFICIARY_ANCHOR_UPDATED."
            "RVT.SUP.002.BENEFICIARY_ANCHOR_UPDATED"
        )
        assert row["payload"]["transition_kind"] == "ARCHIVED"
        assert row["payload"]["anchor_status"] == "ARCHIVED"
        assert row["payload"]["revision"] == 2
        # Validates against the canonical RVT schema.
        validators.rvt.validate_payload(row["payload"])

    async def test_envelope_carries_uuidv7_trio_and_actor(
        self, mint_handler, archive_handler, factory
    ):
        internal_id = await _mint(mint_handler)
        cmd = _archive_cmd(internal_id, command_id="018f8e10-bbbb-7000-8000-000000000001")
        await archive_handler.handle(cmd)
        envelope = factory.outbox.rows[-1]["payload"]["envelope"]
        for f in ("message_id", "correlation_id", "causation_id"):
            assert envelope[f]
        # correlation_id == internal_id; causation_id == command_id.
        assert envelope["correlation_id"] == internal_id
        assert envelope["causation_id"] == "018f8e10-bbbb-7000-8000-000000000001"
        assert envelope["actor"]["kind"] == "human"

    async def test_unknown_internal_id_raises_anchor_not_found(
        self, archive_handler
    ):
        cmd = _archive_cmd(
            "018f8e10-0000-7000-8000-000000000999",
            command_id="018f8e10-bbbb-7000-8000-000000000001",
        )
        with pytest.raises(AnchorNotFound):
            await archive_handler.handle(cmd)

    async def test_already_archived_raises_already_archived(
        self, mint_handler, archive_handler
    ):
        internal_id = await _mint(mint_handler)
        cmd1 = _archive_cmd(internal_id, command_id="018f8e10-bbbb-7000-8000-000000000001")
        await archive_handler.handle(cmd1)
        # Second call with a NEW command_id (so idempotency doesn't catch it).
        cmd2 = _archive_cmd(internal_id, command_id="018f8e10-bbbb-7000-8000-000000000002")
        with pytest.raises(AnchorAlreadyArchived):
            await archive_handler.handle(cmd2)

    async def test_pseudonymised_raises_pseudonymised(
        self, mint_handler, archive_handler, factory
    ):
        internal_id = await _mint(mint_handler)
        # Force the aggregate into the terminal state.
        factory.anchors.rows[internal_id].anchor_status = "PSEUDONYMISED"
        cmd = _archive_cmd(internal_id, command_id="018f8e10-bbbb-7000-8000-000000000001")
        with pytest.raises(AnchorPseudonymised):
            await archive_handler.handle(cmd)

    async def test_idempotent_replay_on_same_command_id(
        self, mint_handler, archive_handler, factory
    ):
        internal_id = await _mint(mint_handler)
        command_id = "018f8e10-bbbb-7000-8000-000000000010"
        first = await archive_handler.handle(_archive_cmd(internal_id, command_id=command_id))
        assert first.http_status == 200
        assert first.idempotent_replay is False

        # Snapshot outbox / idempotency counts.
        outbox_count = len(factory.outbox.rows)
        idem_count = len(factory.idem.rows)

        second = await archive_handler.handle(_archive_cmd(internal_id, command_id=command_id))
        assert second.http_status == 200
        assert second.idempotent_replay is True
        assert second.error_code == "COMMAND_ALREADY_PROCESSED"
        # No second outbox row, no second idempotency row.
        assert len(factory.outbox.rows) == outbox_count
        assert len(factory.idem.rows) == idem_count
        # Snapshot identical to the first call.
        assert second.anchor.internal_id == first.anchor.internal_id
        assert second.anchor.anchor_status == first.anchor.anchor_status
        assert second.anchor.revision == first.anchor.revision

    async def test_idempotency_scope_is_archive(
        self, mint_handler, archive_handler, factory
    ):
        internal_id = await _mint(mint_handler)
        command_id = "018f8e10-bbbb-7000-8000-000000000020"
        await archive_handler.handle(_archive_cmd(internal_id, command_id=command_id))
        scopes = {scope for (scope, _) in factory.idem.rows}
        assert IDEMPOTENCY_SCOPE_ARCHIVE in scopes
        # MINT-scoped row from the earlier mint call is also present.
        assert IDEMPOTENCY_SCOPE_MINT in scopes

    async def test_pii_unchanged_across_archive(
        self, mint_handler, archive_handler, factory
    ):
        internal_id = await _mint(mint_handler)
        pre = factory.anchors.rows[internal_id]
        pre_last_name = pre.pii.last_name
        pre_first_name = pre.pii.first_name
        pre_dob = pre.pii.date_of_birth
        pre_contact = pre.pii.contact_details

        await archive_handler.handle(
            _archive_cmd(internal_id, command_id="018f8e10-bbbb-7000-8000-000000000099")
        )

        post = factory.anchors.rows[internal_id]
        assert post.internal_id.value == internal_id
        assert post.pii.last_name == pre_last_name
        assert post.pii.first_name == pre_first_name
        assert post.pii.date_of_birth == pre_dob
        assert post.pii.contact_details == pre_contact


# ─── Restore handler tests ─────────────────────────────────────────────


class TestRestoreHandler:
    async def test_restore_after_archive_flips_back_to_active(
        self, mint_handler, archive_handler, restore_handler, factory
    ):
        internal_id = await _mint(mint_handler)
        await archive_handler.handle(
            _archive_cmd(internal_id, command_id="018f8e10-bbbb-7000-8000-000000000001")
        )
        result = await restore_handler.handle(
            _restore_cmd(internal_id, command_id="018f8e10-cccc-7000-8000-000000000001")
        )

        assert result.http_status == 200
        assert result.idempotent_replay is False
        assert result.anchor.anchor_status == "ACTIVE"
        assert result.anchor.revision == 3

    async def test_restore_emits_outbox_row_with_restored_kind(
        self, mint_handler, archive_handler, restore_handler, factory, validators
    ):
        internal_id = await _mint(mint_handler)
        await archive_handler.handle(
            _archive_cmd(internal_id, command_id="018f8e10-bbbb-7000-8000-000000000001")
        )
        await restore_handler.handle(
            _restore_cmd(internal_id, command_id="018f8e10-cccc-7000-8000-000000000001")
        )
        row = factory.outbox.rows[-1]
        assert row["payload"]["transition_kind"] == "RESTORED"
        # Per the RVT schema's allOf rule, RESTORED → anchor_status = ACTIVE.
        assert row["payload"]["anchor_status"] == "ACTIVE"
        assert row["payload"]["revision"] == 3
        validators.rvt.validate_payload(row["payload"])

    async def test_restore_on_active_raises_not_archived(
        self, mint_handler, restore_handler
    ):
        internal_id = await _mint(mint_handler)
        with pytest.raises(AnchorNotArchived):
            await restore_handler.handle(
                _restore_cmd(internal_id, command_id="018f8e10-cccc-7000-8000-000000000010")
            )

    async def test_unknown_internal_id_raises_anchor_not_found(
        self, restore_handler
    ):
        with pytest.raises(AnchorNotFound):
            await restore_handler.handle(
                _restore_cmd(
                    "018f8e10-0000-7000-8000-000000000999",
                    command_id="018f8e10-cccc-7000-8000-000000000020",
                )
            )

    async def test_pseudonymised_raises_pseudonymised(
        self, mint_handler, restore_handler, factory
    ):
        internal_id = await _mint(mint_handler)
        factory.anchors.rows[internal_id].anchor_status = "PSEUDONYMISED"
        with pytest.raises(AnchorPseudonymised):
            await restore_handler.handle(
                _restore_cmd(internal_id, command_id="018f8e10-cccc-7000-8000-000000000030")
            )

    async def test_idempotent_replay_on_same_command_id(
        self, mint_handler, archive_handler, restore_handler, factory
    ):
        internal_id = await _mint(mint_handler)
        await archive_handler.handle(
            _archive_cmd(internal_id, command_id="018f8e10-bbbb-7000-8000-000000000001")
        )
        command_id = "018f8e10-cccc-7000-8000-000000000040"
        first = await restore_handler.handle(_restore_cmd(internal_id, command_id=command_id))
        outbox_count = len(factory.outbox.rows)
        idem_count = len(factory.idem.rows)
        second = await restore_handler.handle(_restore_cmd(internal_id, command_id=command_id))
        assert second.idempotent_replay is True
        assert second.error_code == "COMMAND_ALREADY_PROCESSED"
        assert len(factory.outbox.rows) == outbox_count
        assert len(factory.idem.rows) == idem_count
        assert second.anchor.revision == first.anchor.revision

    async def test_idempotency_scope_is_restore(
        self, mint_handler, archive_handler, restore_handler, factory
    ):
        internal_id = await _mint(mint_handler)
        await archive_handler.handle(
            _archive_cmd(internal_id, command_id="018f8e10-bbbb-7000-8000-000000000001")
        )
        await restore_handler.handle(
            _restore_cmd(internal_id, command_id="018f8e10-cccc-7000-8000-000000000050")
        )
        scopes = {scope for (scope, _) in factory.idem.rows}
        assert IDEMPOTENCY_SCOPE_RESTORE in scopes
        assert IDEMPOTENCY_SCOPE_ARCHIVE in scopes
        assert IDEMPOTENCY_SCOPE_MINT in scopes

    async def test_round_trip_active_archived_active(
        self, mint_handler, archive_handler, restore_handler, factory
    ):
        internal_id = await _mint(mint_handler)
        # Three outbox rows expected at the end: MINTED, ARCHIVED, RESTORED.
        assert len(factory.outbox.rows) == 1

        await archive_handler.handle(
            _archive_cmd(internal_id, command_id="018f8e10-bbbb-7000-8000-000000000001")
        )
        assert len(factory.outbox.rows) == 2

        result = await restore_handler.handle(
            _restore_cmd(internal_id, command_id="018f8e10-cccc-7000-8000-000000000001")
        )
        assert len(factory.outbox.rows) == 3
        assert result.anchor.anchor_status == "ACTIVE"
        assert result.anchor.revision == 3

        kinds = [r["payload"]["transition_kind"] for r in factory.outbox.rows]
        assert kinds == ["MINTED", "ARCHIVED", "RESTORED"]


# pytest-asyncio runs in ``auto`` mode (see pyproject.toml) so async test
# functions are picked up without explicit decoration.
