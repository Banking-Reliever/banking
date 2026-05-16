"""Load canonical JSON Schemas from the read-only process/ folder.

The schemas are the source of truth — this service is a *consumer* of them.
Fail-fast at startup if any schema is missing or malformed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator

from ...application.ports import SchemaValidator


# Resolved at startup from settings.PROCESS_SCHEMAS_DIR.
MINT_ANCHOR_SCHEMA_FILE = "CMD.SUP.002.BEN.MINT_ANCHOR.schema.json"
ARCHIVE_ANCHOR_SCHEMA_FILE = "CMD.SUP.002.BEN.ARCHIVE_ANCHOR.schema.json"
RESTORE_ANCHOR_SCHEMA_FILE = "CMD.SUP.002.BEN.RESTORE_ANCHOR.schema.json"
RVT_BENEFICIARY_ANCHOR_UPDATED_SCHEMA_FILE = "RVT.SUP.002.BENEFICIARY_ANCHOR_UPDATED.schema.json"


class JsonSchemaValidator(SchemaValidator):
    def __init__(self, schema: dict[str, Any]) -> None:
        # Will raise SchemaError on a malformed schema — fail-fast.
        Draft202012Validator.check_schema(schema)
        self._validator = Draft202012Validator(
            schema,
            format_checker=Draft202012Validator.FORMAT_CHECKER,
        )

    def validate_payload(self, payload: dict[str, Any]) -> None:
        self._validator.validate(payload)


def load_schema(schemas_dir: Path, filename: str) -> dict[str, Any]:
    path = schemas_dir / filename
    if not path.is_file():
        raise FileNotFoundError(
            f"Required process-layer schema not found: {path}. "
            "This service is a read-only consumer of process/CAP.SUP.002.BEN/schemas/."
        )
    with path.open() as f:
        return json.load(f)


@dataclass(frozen=True, slots=True)
class Validators:
    """Bundle of every JSON Schema validator the service consumes.

    Built once at startup, stored on ``AppState`` and injected into the
    handlers / routers. Each member is a ``JsonSchemaValidator`` —
    swappable in tests via the ``SchemaValidator`` Protocol.
    """

    mint_command: JsonSchemaValidator
    archive_command: JsonSchemaValidator
    restore_command: JsonSchemaValidator
    rvt: JsonSchemaValidator


def build_validators_bundle(schemas_dir: Path) -> Validators:
    """Return the canonical ``Validators`` bundle. Fail-fast on any issue.

    Loads:
      - CMD.MINT_ANCHOR
      - CMD.ARCHIVE_ANCHOR
      - CMD.RESTORE_ANCHOR
      - RVT.BENEFICIARY_ANCHOR_UPDATED
    """
    mint = load_schema(schemas_dir, MINT_ANCHOR_SCHEMA_FILE)
    archive = load_schema(schemas_dir, ARCHIVE_ANCHOR_SCHEMA_FILE)
    restore = load_schema(schemas_dir, RESTORE_ANCHOR_SCHEMA_FILE)
    rvt = load_schema(schemas_dir, RVT_BENEFICIARY_ANCHOR_UPDATED_SCHEMA_FILE)
    return Validators(
        mint_command=JsonSchemaValidator(mint),
        archive_command=JsonSchemaValidator(archive),
        restore_command=JsonSchemaValidator(restore),
        rvt=JsonSchemaValidator(rvt),
    )


def build_validators(schemas_dir: Path) -> tuple[JsonSchemaValidator, JsonSchemaValidator]:
    """Legacy 2-tuple factory — returns ``(mint_cmd_validator, rvt_validator)``.

    Kept for backwards compatibility with TASK-002 tests and code paths that
    pre-date the lifecycle commands. New code should call
    ``build_validators_bundle`` and read fields off ``Validators``.
    """
    bundle = build_validators_bundle(schemas_dir)
    return bundle.mint_command, bundle.rvt


__all__ = [
    "JsonSchemaValidator",
    "Validators",
    "build_validators",
    "build_validators_bundle",
    "MINT_ANCHOR_SCHEMA_FILE",
    "ARCHIVE_ANCHOR_SCHEMA_FILE",
    "RESTORE_ANCHOR_SCHEMA_FILE",
    "RVT_BENEFICIARY_ANCHOR_UPDATED_SCHEMA_FILE",
]
