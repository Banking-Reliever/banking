#!/usr/bin/env python3
"""
BCM export script to EventCatalog.

Usage:
    python bcm_export_metier.py --input /path/to/bcm --output /path/to/eventcatalog
    python bcm_export_metier.py --input /path/to/bcm --output /path/to/eventcatalog --dry-run
    python bcm_export_metier.py --input /path/to/bcm --validate-only
"""

import argparse
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

import yaml

# Import BCM export modules
try:
    # Relative imports when used as a module
    from .parser_bcm import BCMParser
    from .normalizer import BCMNormalizer
    from .eventcatalog_generator import EventCatalogGenerator
except ImportError:
    # Direct imports when used as a standalone script
    from parser_bcm import BCMParser
    from normalizer import BCMNormalizer
    from eventcatalog_generator import EventCatalogGenerator


def setup_logging(verbose: bool = False) -> None:
    """Configures logging."""
    level = logging.DEBUG if verbose else logging.INFO

    # Color-coded format by level
    class ColoredFormatter(logging.Formatter):
        COLORS = {
            'DEBUG': '\033[36m',    # Cyan
            'INFO': '\033[32m',     # Green
            'WARNING': '\033[33m',  # Yellow
            'ERROR': '\033[31m',    # Red
            'CRITICAL': '\033[35m', # Magenta
        }
        RESET = '\033[0m'

        def format(self, record):
            color = self.COLORS.get(record.levelname, '')
            record.levelname = f"{color}{record.levelname}{self.RESET}"
            return super().format(record)

    handler = logging.StreamHandler()
    if sys.stdout.isatty():  # Terminal with colors
        formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
    else:  # Pipe/redirect without colors
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    handler.setFormatter(formatter)

    # Root logger
    logging.basicConfig(level=level, handlers=[handler])

    # Suppress overly verbose yaml logs
    logging.getLogger('yaml').setLevel(logging.WARNING)


def validate_inputs(args: argparse.Namespace) -> None:
    """Validates input arguments."""

    # Validate input directory
    if not args.input_dir:
        raise ValueError("Input directory is required")

    input_path = Path(args.input_dir)
    if not input_path.exists():
        raise ValueError(f"Input directory does not exist: {input_path}")

    if not input_path.is_dir():
        raise ValueError(f"Input path is not a directory: {input_path}")

    # Check for essential BCM files
    l1_file = input_path / "capabilities-L1.yaml"
    if not l1_file.exists():
        raise ValueError(f"Missing L1 capabilities file: {l1_file}")

    # At least one L2 file
    l2_files = list(input_path.glob("capabilities-*-L2.yaml"))
    if not l2_files:
        raise ValueError(f"No L2 capabilities files found in {input_path}")

    # Validate output directory (unless validate-only)
    if not args.validate_only:
        if not args.output_dir:
            raise ValueError("Output directory is required (unless --validate-only)")

        output_path = Path(args.output_dir)

        # Create parent directory if needed
        if not output_path.parent.exists():
            output_path.parent.mkdir(parents=True, exist_ok=True)

        # Verify writability
        if output_path.exists() and not output_path.is_dir():
            raise ValueError(f"Output path exists but is not a directory: {output_path}")


def _slugify(value: str) -> str:
    """Generic EventCatalog-compatible slugification."""
    if not value:
        return "unknown"

    slug = value.lower().replace('_', '-').replace('.', '-')
    slug = ''.join(ch for ch in slug if ch.isalnum() or ch == '-')
    while '--' in slug:
        slug = slug.replace('--', '-')
    slug = slug.strip('-')
    return slug or "unknown"


def _to_bcm_slug(value: str) -> str:
    """Slug following BCM/EventCatalog conventions (CAP/EVT/OBJ/RES)."""
    if not value:
        return "unknown"

    parts = value.split('.')
    if len(parts) >= 3 and parts[-1].isdigit():
        base = '-'.join(parts[-2:])
    elif len(parts) >= 4:
        base = parts[-1]
    else:
        base = value

    return _slugify(base)


def _to_process_slug(value: str) -> str:
    """Slug for PRC processes (includes zone/L1 to avoid collisions)."""
    if not value:
        return "unknown"

    parts = value.split('.')
    if len(parts) >= 5 and parts[0] == 'PRC':
        base = '-'.join(parts[2:])
    else:
        base = value

    return _slugify(base)


def _normalize_owner(owner: str) -> str:
    """Normalizes an owner to a simple slug."""
    if not owner:
        return "unknown-owner"

    value = owner.lower().replace(' & ', ' et ').replace('&', 'et')
    value = value.replace('/', '-').replace(' ', '-')
    value = ''.join(ch for ch in value if ch.isalnum() or ch == '-')
    while '--' in value:
        value = value.replace('--', '-')
    value = value.strip('-')
    return value or "unknown-owner"


def _build_flow_steps(process: Dict[str, Any], event_versions_by_id: Dict[str, str]) -> List[Dict[str, Any]]:
    """Builds EventCatalog steps from the event_subscription_chain."""
    chain = process.get("event_subscription_chain") or []
    steps: List[Dict[str, Any]] = []
    edges: Dict[str, List[str]] = {}

    def _add_edge(source_id: str, target_id: str) -> None:
        if not source_id or not target_id:
            return
        edges.setdefault(source_id, [])
        if target_id not in edges[source_id]:
            edges[source_id].append(target_id)

    start = process.get("start") or {}
    if start.get("type") == "interaction":
        interaction_text = start.get("interaction") or "Business interaction"
        steps.append({
            "id": "START",
            "type": "actor",
            "title": "Process trigger",
            "summary": interaction_text,
            "actor": {
                "name": "Business actor",
                "summary": interaction_text
            }
        })

    step_id_to_step: Dict[str, Dict[str, Any]] = {}
    emitted_event_to_steps: Dict[str, List[str]] = {}
    consumed_event_by_step: Dict[str, str] = {}
    trigger_steps: List[str] = []

    for idx, step in enumerate(chain, start=1):
        step_id = step.get("step_id") or f"STEP.{idx:03d}"
        emitted_event_id = step.get("emits_business_event")
        consumed_event_id = step.get("consumes_business_event")
        consumes_trigger = step.get("consumes_trigger")

        flow_step: Dict[str, Any] = {
            "id": step_id,
            "type": "message",
            "title": step_id,
            "summary": step.get("note") or "Business process step"
        }

        if emitted_event_id:
            flow_step["message"] = {
                "id": _to_bcm_slug(emitted_event_id),
                "version": event_versions_by_id.get(emitted_event_id, "1.0.0")
            }
        else:
            # Fall back to a generic node if no event is emitted
            flow_step["type"] = "node"

        steps.append(flow_step)
        step_id_to_step[step_id] = flow_step

        if emitted_event_id:
            emitted_event_to_steps.setdefault(emitted_event_id, []).append(step_id)

        if isinstance(consumed_event_id, str) and consumed_event_id.strip():
            consumed_event_by_step[step_id] = consumed_event_id.strip()

        if consumes_trigger is not None:
            trigger_steps.append(step_id)

    if "START" in step_id_to_step or any(s.get("id") == "START" for s in steps):
        for target_id in trigger_steps:
            _add_edge("START", target_id)

    for target_step_id, consumed_event in consumed_event_by_step.items():
        producer_steps = emitted_event_to_steps.get(consumed_event, [])
        for producer_step_id in producer_steps:
            _add_edge(producer_step_id, target_step_id)

    for step in steps:
        sid = step.get("id")
        successors = edges.get(sid, [])
        if not successors:
            continue
        if len(successors) == 1:
            step["next_step"] = successors[0]
        else:
            step["next_steps"] = successors

    return steps


def load_processus_metier_as_flows(
    bcm_input_dir: Path,
    bcm_model,
    strict: bool = False,
) -> List[Dict[str, Any]]:
    """Loads external business processes and transforms them into EventCatalog flows."""
    logger = logging.getLogger(__name__)

    repo_root = bcm_input_dir.parent
    processus_dir = repo_root / "externals" / "processus-metier"
    if not processus_dir.exists():
        logger.info(f"No processus-metier directory found at {processus_dir}, skipping flow export")
        return []

    process_files = sorted(processus_dir.glob("processus-metier-*.yaml"))
    if not process_files:
        logger.info(f"No processus-metier files found in {processus_dir}")
        return []

    event_versions_by_id = {
        event.id: event.version
        for event in bcm_model.business_events
    }

    flows: List[Dict[str, Any]] = []

    for file_path in process_files:
        try:
            with open(file_path, "r", encoding="utf-8") as stream:
                data = yaml.safe_load(stream) or {}

            process = data.get("processus_metier") or {}
            if not process:
                if strict:
                    raise ValueError(f"No 'processus_metier' section in {file_path}")
                logger.warning(f"No 'processus_metier' section in {file_path}, skipping")
                continue

            process_type = process.get("process_type")
            if process_type and process_type != "metier":
                logger.debug(f"Skipping non-metier process in {file_path}: {process_type}")
                continue

            process_id = process.get("id") or file_path.stem
            process_name = process.get("name") or process_id
            process_meta = data.get("meta") or {}

            flow_id = _to_process_slug(process_id)
            flow_version = str(process_meta.get("version") or "1.0.0")
            flow_summary = (
                f"Automatic export of business process `{process_id}` to an EventCatalog flow."
            )

            owners_raw = process_meta.get("owners") or []
            owners = [_normalize_owner(owner) for owner in owners_raw if owner]
            if not owners:
                owners = ["unknown-owner"]

            flow_steps = _build_flow_steps(process, event_versions_by_id)
            if not flow_steps:
                if strict:
                    raise ValueError(f"Process {process_id} has no steps")
                logger.warning(f"Process {process_id} has no steps, skipping")
                continue

            flows.append({
                "id": flow_id,
                "name": process_name,
                "version": flow_version,
                "summary": flow_summary,
                "owners": owners,
                "steps": flow_steps,
                "documentation": process.get("documentation") or {},
                "metadata": {
                    "bcm": {
                        "source_id": process_id,
                        "source_file": str(file_path),
                        "bcm_type": "processus_metier",
                        "exported_at": datetime.now().isoformat()
                    }
                }
            })

        except Exception as exc:
            if strict:
                raise
            logger.warning(f"Failed to load processus metier file {file_path}: {exc}")

    return flows


def generate_export_report(parsing_report: Dict, normalization_report: Dict,
                         generation_report: Dict = None) -> Dict[str, Any]:
    """Generates a consolidated export report."""

    report = {
        "export_summary": {
            "exported_at": datetime.now().isoformat(),
            "success": True,
            "total_errors": 0,
            "total_warnings": 0
        },
        "parsing": {
            "source_counts": parsing_report.get_summary(),
            "errors": [],
            "warnings": []
        },
        "normalization": {
            "normalized_counts": normalization_report["metadata"]["normalized_counts"],
            "duration_seconds": normalization_report["metadata"]["duration_seconds"],
            "errors": [],
            "warnings": normalization_report["metadata"].get("warnings", []),
            "missing_relations": normalization_report["metadata"].get("missing_relations", {})
        },
        "generation": None
    }
    
    # Add normalization warnings
    report["export_summary"]["total_warnings"] += len(report["normalization"]["warnings"])

    # Generation report if available
    if generation_report:
        report["generation"] = {
            "files_generated": len(generation_report["files_generated"]),
            "files_list": generation_report["files_generated"],
            "duration_seconds": generation_report["duration_seconds"],
            "errors": generation_report["errors"],
            "warnings": generation_report["warnings"]
        }
        
        report["export_summary"]["total_errors"] += len(generation_report["errors"])
        report["export_summary"]["total_warnings"] += len(generation_report["warnings"])
    
    # Overall status
    report["export_summary"]["success"] = report["export_summary"]["total_errors"] == 0

    return report


def print_summary(report: Dict[str, Any]) -> None:
    """Prints a human-readable summary of the export report."""

    print("\n" + "="*80)
    print("BCM -> EventCatalog EXPORT SUMMARY")
    print("="*80)

    # Overall status
    success = report["export_summary"]["success"]
    status_icon = "[OK]" if success else "[FAIL]"
    print(f"\n{status_icon} Status: {'SUCCESS' if success else 'FAILURE'}")

    # Main statistics
    parsing = report["parsing"]["source_counts"]
    normalization = report["normalization"]["normalized_counts"]

    print(f"\nBCM sources analysed:")
    print(f"   * L1 capabilities: {parsing['capabilities_l1']}")
    print(f"   * L2 capabilities: {parsing['capabilities_l2']}")
    print(f"   * Business events: {parsing['business_events']}")
    print(f"   * Business objects: {parsing['business_objects']}")
    if 'business_concepts' in parsing:
        print(f"   * Business concepts: {parsing['business_concepts']}")
    if 'business_subscriptions' in parsing:
        print(f"   * Business subscriptions: {parsing['business_subscriptions']}")

    print(f"\nEventCatalog artefacts generated:")
    print(f"   * Domains: {normalization['domains']}")
    print(f"   * Services: {normalization['services']}")
    print(f"   * Events: {normalization['events']}")
    print(f"   * Entities: {normalization['entities']}")
    if 'flows' in normalization:
        print(f"   * Flows: {normalization['flows']}")
    if 'concepts' in normalization:
        print(f"   * Concepts: {normalization['concepts']}")
    if 'subscriptions' in normalization:
        print(f"   * Subscriptions: {normalization['subscriptions']}")

    # Generated files
    if report["generation"]:
        files_count = report["generation"]["files_generated"]
        print(f"\nFiles created: {files_count}")

        duration = report["generation"]["duration_seconds"]
        print(f"Generation time: {duration:.2f}s")

    # Errors and warnings
    total_errors = report["export_summary"]["total_errors"]
    total_warnings = report["export_summary"]["total_warnings"]

    if total_errors > 0:
        print(f"\nErrors: {total_errors}")

    if total_warnings > 0:
        print(f"\nWarnings: {total_warnings}")

    # Missing relations
    missing_relations = report["normalization"]["missing_relations"]
    if missing_relations:
        print(f"\nMissing relations detected:")
        for rel_type, items in missing_relations.items():
            if items:
                print(f"   * {rel_type}: {len(items)} elements")

    print("\n" + "="*80)


def main():
    """Main entry point of the script."""

    # CLI arguments
    parser = argparse.ArgumentParser(
        description="Export BCM to EventCatalog",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input ./bcm --output ./views/FOODAROO-Metier
  %(prog)s --input ./bcm --output ./views/FOODAROO-Metier --dry-run
  %(prog)s --input ./bcm --validate-only --verbose
        """
    )

    parser.add_argument(
        "--input", "-i",
        dest="input_dir",
        required=True,
        help="Source directory containing BCM YAML files"
    )

    parser.add_argument(
        "--output", "-o",
        dest="output_dir",
        help="Output directory for the EventCatalog (required unless --validate-only)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the export without writing any files"
    )

    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate BCM data only without generating the EventCatalog"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose mode"
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: every warning is treated as a blocking error"
    )

    parser.add_argument(
        "--report-json",
        metavar="FILE",
        help="Save the detailed report as JSON"
    )

    parser.add_argument(
        "--report-md",
        metavar="FILE",
        help="Save the detailed report as Markdown"
    )
    
    args = parser.parse_args()

    # Logging setup
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    try:
        # Validate inputs
        logger.info("Validating input parameters...")
        validate_inputs(args)

        # Parse BCM
        logger.info("Parsing BCM files...")
        bcm_parser = BCMParser(strict=args.strict)
        bcm_model = bcm_parser.parse_bcm_directory(Path(args.input_dir))

        # Validate model
        logger.info("Validating model consistency...")
        validation_errors = bcm_model.validate_all()

        if validation_errors:
            logger.warning("Validation errors detected:")
            for error_type, errors in validation_errors.items():
                for error in errors:
                    logger.warning(f"  {error_type}: {error}")
            if args.strict:
                logger.error("[strict] Validation errors detected")
                return 1

        # Stop here if validate-only
        if args.validate_only:
            logger.info("Validation complete")
            summary = bcm_model.get_summary()
            print(f"\nBCM model validated: {summary}")
            if validation_errors:
                print(f"WARNING: {sum(len(errs) for errs in validation_errors.values())} error(s) found")
                return 1
            return 0

        # Normalisation
        logger.info("Normalizing BCM data...")
        normalizer = BCMNormalizer()
        normalized_data = normalizer.normalize_model(bcm_model)

        # Load external business processes and inject as EventCatalog flows
        logger.info("Loading external business processes for flow export...")
        flow_data = load_processus_metier_as_flows(
            Path(args.input_dir),
            bcm_model,
            strict=args.strict,
        )
        normalized_data["flows"] = flow_data
        normalized_data["metadata"]["normalized_counts"]["flows"] = len(flow_data)

        # Generate EventCatalog (unless dry-run)
        generation_report = None
        if not args.dry_run:
            logger.info("Generating EventCatalog...")
            generator = EventCatalogGenerator(Path(args.output_dir))
            generation_report = generator.generate_catalog(normalized_data)
        else:
            logger.info("Dry-run mode: simulating without writing files")

        # Consolidated report
        full_report = generate_export_report(
            bcm_model, normalized_data, generation_report
        )

        # Print summary
        print_summary(full_report)

        if args.strict and full_report["export_summary"]["total_warnings"] > 0:
            logger.error(
                "[strict] %s warning(s) detected",
                full_report["export_summary"]["total_warnings"],
            )
            return 1

        # Save reports
        if args.report_json:
            with open(args.report_json, 'w', encoding='utf-8') as f:
                json.dump(full_report, f, indent=2, ensure_ascii=False)
            logger.info(f"JSON report saved: {args.report_json}")

        if args.report_md:
            # TODO: Implement Markdown report generation
            logger.warning("Markdown report generation not yet implemented")

        # Return code
        success = full_report["export_summary"]["success"]
        logger.info(f"Export {'succeeded' if success else 'failed'}")

        return 0 if success else 1

    except KeyboardInterrupt:
        logger.error("Export interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if args.verbose:
            import traceback
            logger.error(f"Details: {traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())