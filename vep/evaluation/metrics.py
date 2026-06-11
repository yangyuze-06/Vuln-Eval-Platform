"""VEP Evaluation: Metrics output utilities.

Phase 2: Unified Evaluation Core
Convert EvalResult to dict and write metrics JSON.
"""

import json
from pathlib import Path

from vep.core.models import EvalResult


def eval_result_to_dict(result: EvalResult) -> dict:
    """Convert EvalResult to dictionary for JSON serialization.

    Output format compatible with existing metrics.json files,
    with additional v2 fields marked with schema_version.

    Args:
        result: EvalResult object

    Returns:
        Dictionary ready for JSON serialization
    """
    metrics = {
        "tool": result.tool,
        "cwe": result.cwe,
        "tp": result.tp,
        "fp": result.fp,
        "fn": result.fn,
        "precision": result.precision,
        "recall": result.recall,
        "f1": result.f1,
        "schema_version": result.schema_version,
        "total_findings": result.total_findings,
        "total_expected_vulnerable": result.total_expected_vulnerable,
    }

    # Optional fields
    if result.tn is not None:
        metrics["tn"] = result.tn
    if result.total_expected_cases is not None:
        metrics["total_expected_cases"] = result.total_expected_cases

    return metrics


def write_metrics_json(result: EvalResult, path: Path) -> None:
    """Write evaluation metrics to JSON file.

    Creates parent directories if needed.
    Output format: UTF-8, 2-space indent.

    Args:
        result: EvalResult to serialize
        path: Output file path

    Raises:
        IOError: If file cannot be written
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    metrics = eval_result_to_dict(result)

    with path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
        f.write("\n")  # Trailing newline
