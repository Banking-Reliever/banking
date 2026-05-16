"""End-to-end integration test for ARCHIVE + RESTORE — runs the FastAPI app
in-process against the docker-compose Postgres + RabbitMQ.

Covers DoD items:
  - POST /anchors/{id}/archive 200 / 400 / 404 / 409 paths
  - POST /anchors/{id}/restore 200 / 404 / 409 paths
  - ACTIVE → ARCHIVED → ACTIVE round-trip with revision monotonicity
  - GET continues to resolve archived anchors (visible anchor_status = ARCHIVED)
  - ETag changes on every transition
  - Idempotency on command_id within the 30-day window
  - Exactly one outbox row per accepted transition; transition_kind set correctly
  - PRJ.ANCHOR_DIRECTORY ingests both transition kinds via LWW upsert
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from reliever_beneficiary_anchor.presentation.app import create_app

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def client(app_settings, reset_db):
    app = create_app(app_settings)
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


def _crid() -> str:
    return f"018f8e10-eeee-7{uuid.uuid4().hex[1:4]}-8{uuid.uuid4().hex[1:4]}-{uuid.uuid4().hex[:12]}"


def _command_id() -> str:
    return f"018f8e10-cccc-7{uuid.uuid4().hex[1:4]}-8{uuid.uuid4().hex[1:4]}-{uuid.uuid4().hex[:12]}"


def _mint_body(crid: str | None = None) -> dict:
    return {
        "client_request_id": crid or _crid(),
        "last_name": "Dupont",
        "first_name": "Marie",
        "date_of_birth": "1985-06-21",
        "contact_details": {"email": "marie.dupont@example.org"},
    }


async def _mint(client) -> dict:
    resp = await client.post("/anchors", json=_mint_body())
    assert resp.status_code == 201, resp.text
    return resp.json()


# ─── ARCHIVE happy path ───────────────────────────────────────────────


async def test_archive_active_anchor_returns_200(client):
    anchor = await _mint(client)
    internal_id = anchor["internal_id"]
    resp = await client.post(
        f"/anchors/{internal_id}/archive",
        json={"command_id": _command_id(), "reason": "PROGRAMME_EXIT_SUCCESS"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["anchor_status"] == "ARCHIVED"
    assert body["revision"] == 2
    # PII unchanged.
    assert body["last_name"] == "Dupont"
    assert body["first_name"] == "Marie"


async def test_archive_then_get_returns_archived_anchor(client):
    anchor = await _mint(client)
    internal_id = anchor["internal_id"]

    archive_resp = await client.post(
        f"/anchors/{internal_id}/archive",
        json={"command_id": _command_id(), "reason": "PROGRAMME_EXIT_SUCCESS"},
    )
    assert archive_resp.status_code == 200

    # The GET serves from the projection. Wait for it to catch up to revision >= 2.
    final = None
    for _ in range(50):
        resp = await client.get(f"/anchors/{internal_id}")
        if resp.status_code == 200 and resp.json().get("revision", 0) >= 2:
            final = resp
            break
        await asyncio.sleep(0.1)
    assert final is not None, "projection did not catch up to revision 2"
    body = final.json()
    assert body["anchor_status"] == "ARCHIVED"
    assert body["revision"] == 2


async def test_etag_changes_on_transition(client):
    anchor = await _mint(client)
    internal_id = anchor["internal_id"]

    # Wait for the MINT projection.
    etag_before = None
    for _ in range(50):
        resp = await client.get(f"/anchors/{internal_id}")
        if resp.status_code == 200:
            etag_before = resp.headers["ETag"]
            break
        await asyncio.sleep(0.1)
    assert etag_before is not None

    await client.post(
        f"/anchors/{internal_id}/archive",
        json={"command_id": _command_id(), "reason": "PROGRAMME_EXIT_SUCCESS"},
    )

    etag_after = None
    for _ in range(50):
        resp = await client.get(f"/anchors/{internal_id}")
        if resp.status_code == 200 and resp.headers["ETag"] != etag_before:
            etag_after = resp.headers["ETag"]
            break
        await asyncio.sleep(0.1)
    assert etag_after is not None and etag_after != etag_before


# ─── ARCHIVE error paths ──────────────────────────────────────────────


async def test_archive_missing_reason_returns_400(client):
    anchor = await _mint(client)
    internal_id = anchor["internal_id"]
    resp = await client.post(
        f"/anchors/{internal_id}/archive",
        json={"command_id": _command_id()},
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "INVALID_PAYLOAD"


async def test_archive_invalid_reason_returns_400(client):
    anchor = await _mint(client)
    internal_id = anchor["internal_id"]
    resp = await client.post(
        f"/anchors/{internal_id}/archive",
        json={"command_id": _command_id(), "reason": "NOT_A_VALID_REASON"},
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "INVALID_PAYLOAD"


async def test_archive_unknown_internal_id_returns_404(client):
    resp = await client.post(
        "/anchors/018f8e10-0000-7000-8000-000000000999/archive",
        json={"command_id": _command_id(), "reason": "PROGRAMME_EXIT_SUCCESS"},
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "ANCHOR_NOT_FOUND"


async def test_archive_already_archived_returns_409(client):
    anchor = await _mint(client)
    internal_id = anchor["internal_id"]
    first = await client.post(
        f"/anchors/{internal_id}/archive",
        json={"command_id": _command_id(), "reason": "PROGRAMME_EXIT_SUCCESS"},
    )
    assert first.status_code == 200
    second = await client.post(
        f"/anchors/{internal_id}/archive",
        json={"command_id": _command_id(), "reason": "PROGRAMME_EXIT_SUCCESS"},
    )
    assert second.status_code == 409
    assert second.json()["error_code"] == "ANCHOR_ALREADY_ARCHIVED"


# ─── ARCHIVE idempotency ──────────────────────────────────────────────


async def test_archive_idempotent_on_same_command_id(client):
    anchor = await _mint(client)
    internal_id = anchor["internal_id"]
    cmd_id = _command_id()
    first = await client.post(
        f"/anchors/{internal_id}/archive",
        json={"command_id": cmd_id, "reason": "PROGRAMME_EXIT_SUCCESS"},
    )
    assert first.status_code == 200
    first_body = first.json()
    second = await client.post(
        f"/anchors/{internal_id}/archive",
        json={"command_id": cmd_id, "reason": "PROGRAMME_EXIT_SUCCESS"},
    )
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["error_code"] == "COMMAND_ALREADY_PROCESSED"
    assert second_body["anchor"]["revision"] == first_body["revision"]


async def test_archive_idempotent_does_not_emit_second_outbox(client, pg_dsn):
    import psycopg

    anchor = await _mint(client)
    internal_id = anchor["internal_id"]
    cmd_id = _command_id()
    await client.post(
        f"/anchors/{internal_id}/archive",
        json={"command_id": cmd_id, "reason": "PROGRAMME_EXIT_SUCCESS"},
    )
    await client.post(
        f"/anchors/{internal_id}/archive",
        json={"command_id": cmd_id, "reason": "PROGRAMME_EXIT_SUCCESS"},
    )

    # Count outbox rows for this anchor whose transition_kind is ARCHIVED.
    async with await psycopg.AsyncConnection.connect(pg_dsn) as conn, conn.cursor() as cur:
        await cur.execute(
            """
            SELECT COUNT(*) FROM outbox
            WHERE correlation_id = %s
              AND payload->>'transition_kind' = 'ARCHIVED'
            """,
            (internal_id,),
        )
        (count,) = await cur.fetchone()  # type: ignore[misc]
    assert count == 1, f"expected exactly one ARCHIVED outbox row, got {count}"


# ─── RESTORE happy path ───────────────────────────────────────────────


async def test_restore_archived_anchor_returns_200(client):
    anchor = await _mint(client)
    internal_id = anchor["internal_id"]
    await client.post(
        f"/anchors/{internal_id}/archive",
        json={"command_id": _command_id(), "reason": "PROGRAMME_EXIT_SUCCESS"},
    )
    resp = await client.post(
        f"/anchors/{internal_id}/restore",
        json={"command_id": _command_id(), "reason": "ARCHIVED_IN_ERROR"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["anchor_status"] == "ACTIVE"
    assert body["revision"] == 3


async def test_round_trip_active_archived_active(client):
    anchor = await _mint(client)
    internal_id = anchor["internal_id"]

    archive_resp = await client.post(
        f"/anchors/{internal_id}/archive",
        json={"command_id": _command_id(), "reason": "PROGRAMME_EXIT_SUCCESS"},
    )
    assert archive_resp.status_code == 200
    assert archive_resp.json()["anchor_status"] == "ARCHIVED"
    assert archive_resp.json()["revision"] == 2

    restore_resp = await client.post(
        f"/anchors/{internal_id}/restore",
        json={"command_id": _command_id(), "reason": "ARCHIVED_IN_ERROR"},
    )
    assert restore_resp.status_code == 200
    assert restore_resp.json()["anchor_status"] == "ACTIVE"
    assert restore_resp.json()["revision"] == 3

    # Projection eventually reflects ACTIVE@rev=3.
    final = None
    for _ in range(50):
        resp = await client.get(f"/anchors/{internal_id}")
        if resp.status_code == 200 and resp.json().get("revision", 0) >= 3:
            final = resp
            break
        await asyncio.sleep(0.1)
    assert final is not None
    assert final.json()["anchor_status"] == "ACTIVE"
    assert final.json()["revision"] == 3


# ─── RESTORE error paths ──────────────────────────────────────────────


async def test_restore_unknown_internal_id_returns_404(client):
    resp = await client.post(
        "/anchors/018f8e10-0000-7000-8000-000000000999/restore",
        json={"command_id": _command_id(), "reason": "ARCHIVED_IN_ERROR"},
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "ANCHOR_NOT_FOUND"


async def test_restore_on_active_returns_409_not_archived(client):
    anchor = await _mint(client)
    internal_id = anchor["internal_id"]
    resp = await client.post(
        f"/anchors/{internal_id}/restore",
        json={"command_id": _command_id(), "reason": "ARCHIVED_IN_ERROR"},
    )
    assert resp.status_code == 409
    assert resp.json()["error_code"] == "ANCHOR_NOT_ARCHIVED"


async def test_restore_idempotent_on_same_command_id(client):
    anchor = await _mint(client)
    internal_id = anchor["internal_id"]
    await client.post(
        f"/anchors/{internal_id}/archive",
        json={"command_id": _command_id(), "reason": "PROGRAMME_EXIT_SUCCESS"},
    )
    cmd_id = _command_id()
    first = await client.post(
        f"/anchors/{internal_id}/restore",
        json={"command_id": cmd_id, "reason": "ARCHIVED_IN_ERROR"},
    )
    assert first.status_code == 200
    second = await client.post(
        f"/anchors/{internal_id}/restore",
        json={"command_id": cmd_id, "reason": "ARCHIVED_IN_ERROR"},
    )
    assert second.status_code == 200
    assert second.json()["error_code"] == "COMMAND_ALREADY_PROCESSED"


# ─── PRJ.ANCHOR_DIRECTORY — LWW upsert ────────────────────────────────


async def test_projection_ingests_both_archived_and_restored(client, pg_dsn):
    import psycopg
    from psycopg.rows import dict_row

    anchor = await _mint(client)
    internal_id = anchor["internal_id"]
    await client.post(
        f"/anchors/{internal_id}/archive",
        json={"command_id": _command_id(), "reason": "PROGRAMME_EXIT_SUCCESS"},
    )
    await client.post(
        f"/anchors/{internal_id}/restore",
        json={"command_id": _command_id(), "reason": "ARCHIVED_IN_ERROR"},
    )

    # Wait for revision=3 in the projection.
    rev = 0
    for _ in range(50):
        async with await psycopg.AsyncConnection.connect(pg_dsn) as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT revision, anchor_status FROM anchor_directory WHERE internal_id = %s",
                (internal_id,),
            )
            row = await cur.fetchone()
            if row is not None and row["revision"] >= 3:
                rev = row["revision"]
                status = row["anchor_status"]
                break
        await asyncio.sleep(0.1)
    assert rev == 3
    assert status == "ACTIVE"


async def test_projection_drops_out_of_order_lower_revision(client, pg_dsn):
    """LWW upsert: a write of revision N with N <= stored revision is dropped.

    We simulate by directly upserting a stale revision into the directory
    and asserting the row's revision does not regress.
    """
    import psycopg
    from psycopg.rows import dict_row
    from reliever_beneficiary_anchor.infrastructure.persistence.projection import (
        PostgresAnchorDirectoryWriter,
    )
    from psycopg_pool import AsyncConnectionPool

    anchor = await _mint(client)
    internal_id = anchor["internal_id"]
    await client.post(
        f"/anchors/{internal_id}/archive",
        json={"command_id": _command_id(), "reason": "PROGRAMME_EXIT_SUCCESS"},
    )

    # Wait for revision=2 in the projection.
    for _ in range(50):
        async with await psycopg.AsyncConnection.connect(pg_dsn) as conn, conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                "SELECT revision FROM anchor_directory WHERE internal_id = %s",
                (internal_id,),
            )
            row = await cur.fetchone()
            if row is not None and row["revision"] >= 2:
                break
        await asyncio.sleep(0.1)
    else:  # pragma: no cover — defensive
        pytest.fail("projection did not reach revision 2")

    # Attempt a stale write at revision=1.
    pool = AsyncConnectionPool(pg_dsn, min_size=1, max_size=2, open=False)
    await pool.open()
    try:
        writer = PostgresAnchorDirectoryWriter(pool)
        applied = await writer.upsert(
            {
                "internal_id": internal_id,
                "last_name": "Stale",
                "first_name": "Stale",
                "date_of_birth": "1985-06-21",
                "contact_details": None,
                "anchor_status": "ACTIVE",
                "creation_date": "2025-01-01",
                "pseudonymized_at": None,
                "revision": 1,
            }
        )
        assert applied is False
    finally:
        await pool.close()

    # Verify the stored row was NOT rewritten.
    async with await psycopg.AsyncConnection.connect(pg_dsn) as conn, conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT revision, anchor_status, last_name FROM anchor_directory WHERE internal_id = %s",
            (internal_id,),
        )
        row = await cur.fetchone()
    assert row is not None
    assert row["revision"] == 2
    assert row["anchor_status"] == "ARCHIVED"
    assert row["last_name"] == "Dupont"  # unchanged from the live state


# ─── Validity of body shape ───────────────────────────────────────────


async def test_archive_extra_field_returns_400(client):
    """The canonical schema declares additionalProperties: false."""
    anchor = await _mint(client)
    internal_id = anchor["internal_id"]
    resp = await client.post(
        f"/anchors/{internal_id}/archive",
        json={
            "command_id": _command_id(),
            "reason": "PROGRAMME_EXIT_SUCCESS",
            "rogue_field": "not allowed",
        },
    )
    assert resp.status_code == 400
    assert resp.json()["error_code"] == "INVALID_PAYLOAD"
