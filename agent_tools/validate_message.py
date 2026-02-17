#!/usr/bin/env python3
"""
Inter-agent Message Validator

Validates inter-agent messages against defined JSON schemas.

Usage:
    python validate_message.py <message_file> [--schema <schema_file>]
    python validate_message.py <message_file> --type <envelope|plan|report|config|user_task>

Examples:
    python validate_message.py task_envelope.json --type envelope
    python validate_message.py task_plan.json --schema agent/agent_protocol/schemas/task_plan.schema.json

Returns:
    Exit code 0 if valid, 1 if invalid
    Outputs validation report to stdout
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from agent_tools._schema_utils import (
        HAS_JSONSCHEMA,
        canonical_schema_type,
        detect_schema_type,
        get_builtin_schema_path,
        iter_validation_errors,
        load_data_file,
    )
except ImportError:
    from _schema_utils import (  # type: ignore
        HAS_JSONSCHEMA,
        canonical_schema_type,
        detect_schema_type,
        get_builtin_schema_path,
        iter_validation_errors,
        load_data_file,
    )

try:
    from jsonschema import ValidationError
except Exception:  # pragma: no cover
    ValidationError = Exception  # type: ignore[assignment]


def calculate_checksum(payload: dict[str, Any]) -> str:
    """Calculate SHA-256 checksum of payload."""
    payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload_str.encode()).hexdigest()


def validate_checksum(message: dict[str, Any]) -> tuple[bool, str]:
    """Validate the checksum in a message envelope."""
    if "validation" not in message or "checksum" not in message.get("validation", {}):
        return True, "No checksum to validate"

    if "payload" not in message:
        return False, "Message has checksum but no payload"

    expected = message["validation"]["checksum"]
    actual = calculate_checksum(message["payload"])

    if expected == actual:
        return True, "Checksum valid"
    else:
        return False, f"Checksum mismatch: expected {expected}, got {actual}"


def validate_references(message: dict[str, Any]) -> list[str]:
    """Validate internal references in a task plan."""
    warnings = []

    if "action_plan" not in message:
        return warnings

    # Collect all action IDs
    action_ids = {action.get("action_id") for action in message.get("action_plan", [])}

    # Check dependencies reference valid actions
    for action in message.get("action_plan", []):
        for dep_id in action.get("depends_on", []):
            if dep_id not in action_ids:
                warnings.append(f"Action {action.get('action_id')} depends on unknown action: {dep_id}")

    # Check subtask references
    for subtask in message.get("task_decomposition", []):
        for action_id in subtask.get("actions", []):
            if action_id not in action_ids:
                warnings.append(f"Subtask {subtask.get('subtask_id')} references unknown action: {action_id}")

    return warnings


def check_dependency_cycles(message: dict[str, Any]) -> list[str]:
    """Check for circular dependencies in action plan."""
    errors = []

    if "action_plan" not in message:
        return errors

    # Build dependency graph
    graph: dict[str, list[str]] = {}
    for action in message.get("action_plan", []):
        action_id = action.get("action_id")
        graph[action_id] = action.get("depends_on", [])

    # DFS cycle detection
    visited: set[str] = set()
    rec_stack: set[str] = set()

    def has_cycle(node: str) -> bool:
        visited.add(node)
        rec_stack.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(node)
        return False

    for node in graph:
        if node not in visited:
            if has_cycle(node):
                errors.append(f"Circular dependency detected involving action: {node}")
                break

    return errors


def format_validation_error(error: ValidationError) -> str:
    """Format a validation error for display."""
    path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
    return f"  [{path}] {error.message}"


def validate_message(
    message_path: Path,
    schema_path: Path | None = None,
    schema_type: str | None = None,
) -> tuple[bool, dict[str, Any]]:
    """
    Validate a message against a schema.

    Returns:
        Tuple of (is_valid, report)
    """
    report: dict[str, Any] = {
        "file": str(message_path),
        "timestamp": datetime.now().isoformat(),
        "valid": False,
        "errors": [],
        "warnings": [],
        "checks_performed": [],
    }

    # Load message
    try:
        message = load_data_file(message_path)
        report["checks_performed"].append("File loaded successfully")
    except Exception as e:
        report["errors"].append(f"Failed to load message file: {e}")
        return False, report

    # Determine schema
    if schema_path is None and schema_type is None:
        detected = detect_schema_type(message)
        if not detected:
            report["errors"].append("Cannot auto-detect schema type. Please specify --type or --schema")
            return False, report
        schema_type = detected
    elif schema_type is not None:
        schema_type = canonical_schema_type(schema_type)

    if schema_path is None:
        schema_path = get_builtin_schema_path(schema_type)

    report["schema"] = str(schema_path)
    report["schema_type"] = schema_type

    # Load schema
    try:
        schema = load_data_file(schema_path)
        report["checks_performed"].append("Schema loaded successfully")
    except Exception as e:
        report["errors"].append(f"Failed to load schema: {e}")
        return False, report

    # JSON Schema validation
    if HAS_JSONSCHEMA:
        try:
            errors = iter_validation_errors(message, schema)

            if errors:
                report["errors"].extend(format_validation_error(e) for e in errors)
            else:
                report["checks_performed"].append("JSON Schema validation passed")
        except Exception as e:
            report["errors"].append(f"Schema validation error: {e}")
    else:
        report["warnings"].append("jsonschema not installed. Schema validation skipped.")

    # Checksum validation (for envelopes)
    if schema_type == "envelope":
        checksum_valid, checksum_msg = validate_checksum(message)
        if checksum_valid:
            report["checks_performed"].append(f"Checksum: {checksum_msg}")
        else:
            report["errors"].append(f"Checksum: {checksum_msg}")

    # Reference validation (for plans)
    if schema_type == "plan":
        # Backward compatibility for existing validate_message semantics.
        schema_type = "task_plan"
    if schema_type == "task_plan":
        ref_warnings = validate_references(message)
        report["warnings"].extend(ref_warnings)
        if not ref_warnings:
            report["checks_performed"].append("Internal references valid")

        cycle_errors = check_dependency_cycles(message)
        report["errors"].extend(cycle_errors)
        if not cycle_errors:
            report["checks_performed"].append("No dependency cycles detected")

    # Determine overall validity
    report["valid"] = len(report["errors"]) == 0

    return report["valid"], report


def print_report(report: dict[str, Any], verbose: bool = False) -> None:
    """Print validation report to stdout."""
    status = "VALID" if report["valid"] else "INVALID"
    print(f"\n{'=' * 60}")
    print(f"Validation Report: {status}")
    print(f"{'=' * 60}")
    print(f"File: {report['file']}")
    print(f"Schema: {report.get('schema', 'N/A')}")
    print(f"Type: {report.get('schema_type', 'N/A')}")
    print(f"Timestamp: {report['timestamp']}")

    if report["errors"]:
        print(f"\nErrors ({len(report['errors'])}):")
        for error in report["errors"]:
            print(f"  - {error}")

    if report["warnings"]:
        print(f"\nWarnings ({len(report['warnings'])}):")
        for warning in report["warnings"]:
            print(f"  - {warning}")

    if verbose and report["checks_performed"]:
        print(f"\nChecks Performed ({len(report['checks_performed'])}):")
        for check in report["checks_performed"]:
            print(f"  + {check}")

    print(f"\n{'=' * 60}\n")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate inter-agent messages against JSON schemas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s task_envelope.json --type envelope
  %(prog)s task_plan.json --type plan
  %(prog)s config.yaml --schema custom_schema.json
  %(prog)s message.json --verbose
        """,
    )
    parser.add_argument("message_file", type=Path, help="Path to the message file to validate")
    parser.add_argument(
        "--schema",
        type=Path,
        help="Path to custom schema file",
    )
    parser.add_argument(
        "--type",
        choices=sorted(set(["envelope", "plan", "report", "config", "user_task", "task_plan", "system_config"])),
        help="Built-in schema type to use",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed validation report",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output report as JSON",
    )

    args = parser.parse_args()

    if not args.message_file.exists():
        print(f"Error: File not found: {args.message_file}", file=sys.stderr)
        return 1

    is_valid, report = validate_message(
        args.message_file,
        schema_path=args.schema,
        schema_type=args.type,
    )

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report, verbose=args.verbose)

    return 0 if is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
