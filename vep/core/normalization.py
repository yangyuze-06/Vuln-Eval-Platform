"""VEP Core: Normalization utilities for CWE and testcase identifiers.

Phase 2: Unified Evaluation Core
Functions for standardizing CWE IDs and testcase names across different formats.
"""

import re
from typing import Optional


# Regex patterns
BENCHMARK_RE = re.compile(r"BenchmarkTest(\d+)")
CWE_RE = re.compile(r"(?i)(?:cwe[-_ ]*)?0*(\d+)([a-z]*)")


def normalize_cwe_id(value: str) -> str:
    """Normalize CWE identifier to standard format CWE-XXX or CWE-XXX{suffix}.

    Examples:
        "CWE-022" -> "CWE-022"
        "022" -> "CWE-022"
        "22" -> "CWE-022"
        "cwe022" -> "CWE-022"
        "cwe-022" -> "CWE-022"
        "CWE_022" -> "CWE-022"
        "328S" -> "CWE-328S"
        "CWE-328_328S" -> "CWE-328" (strips special suffix)

    Args:
        value: CWE identifier in any format

    Returns:
        Normalized CWE identifier (CWE-XXX or CWE-XXX{suffix})

    Note:
        For CWE-328_328S special case in CodeQL, we normalize to CWE-328
        to match the manifest convention. The "S" suffix variant is handled
        separately in the ground truth loader.
    """
    if not value:
        return ""

    # Handle CWE-328_328S special case
    if "328_328S" in value.upper():
        return "CWE-328"

    match = CWE_RE.search(str(value))
    if not match:
        return value  # Preserve original if no match

    number = int(match.group(1))
    suffix = match.group(2).upper()

    if suffix:
        return f"CWE-{number:03d}{suffix}"
    else:
        return f"CWE-{number:03d}"


def short_cwe_id(value: str) -> str:
    """Extract short CWE ID (numeric only) from any CWE format.

    Examples:
        "CWE-022" -> "022"
        "cwe022" -> "022"
        "22" -> "022"
        "CWE-328S" -> "328"

    Args:
        value: CWE identifier in any format

    Returns:
        Zero-padded 3-digit CWE number (e.g., "022")
    """
    match = CWE_RE.search(str(value))
    if not match:
        return ""

    number = int(match.group(1))
    return f"{number:03d}"


def normalize_testcase_id(value: str) -> str:
    """Extract normalized testcase identifier from various formats.

    Examples:
        "BenchmarkTest00001" -> "BenchmarkTest00001"
        "org/owasp/benchmark/BenchmarkTest00001.java" -> "BenchmarkTest00001"
        "/path/to/BenchmarkTest00001.java" -> "BenchmarkTest00001"

    Args:
        value: Testcase identifier or file path

    Returns:
        Normalized testcase identifier (e.g., "BenchmarkTest00001")
        Returns original value if no match found.
    """
    if not value:
        return ""

    match = BENCHMARK_RE.search(str(value))
    if match:
        # Extract full BenchmarkTestXXXXX
        number = match.group(1)
        return f"BenchmarkTest{number}"

    # No match, return original (preserves non-benchmark testcases)
    return str(value).strip()


def safe_int(value) -> Optional[int]:
    """Safely convert value to int, returning None on failure.

    Args:
        value: Value to convert (any type)

    Returns:
        Integer value or None if conversion fails
    """
    if value is None:
        return None
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def normalize_truth_value(value: str) -> Optional[bool]:
    """Normalize truth value from ground truth CSV.

    Supports: true/false, 1/0, yes/no, positive/negative, vulnerable/safe.

    Args:
        value: Truth value string

    Returns:
        True for positive, False for negative, None if ambiguous
    """
    if not value:
        return None

    normalized = str(value).strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "", normalized)

    positive_values = {
        "1", "true", "positive", "vulnerable", "yes", "y", "real", "tp"
    }
    negative_values = {
        "0", "false", "negative", "safe", "no", "n", "notvulnerable", "fp"
    }

    if normalized in positive_values:
        return True
    elif normalized in negative_values:
        return False
    else:
        return None
