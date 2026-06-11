"""VEP Core: Data models for unified evaluation.

Phase 2: Unified Evaluation Core
Standard library dataclasses for findings, expected cases, and evaluation results.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Finding:
    """Represents a single vulnerability finding from a static analysis tool.

    Attributes:
        testcase: Benchmark test case identifier (e.g., "BenchmarkTest00001")
        rule_id: Rule or CWE identifier (e.g., "CWE-022")
        file: Source file path
        line: Line number (optional)
        tool: Tool name (e.g., "codefuse", "codeql")
        cwe: CWE identifier (optional, may differ from rule_id)
        message: Finding message or reason (optional)
        raw: Original data for extension fields
    """
    testcase: str
    rule_id: str
    file: str
    line: Optional[int] = None
    tool: Optional[str] = None
    cwe: Optional[str] = None
    message: Optional[str] = None
    raw: dict = field(default_factory=dict)


@dataclass
class ExpectedCase:
    """Represents a ground truth test case from OWASP Benchmark.

    Attributes:
        testcase: Test case identifier
        cwe: CWE identifier
        is_vulnerable: True if this is a true positive case
        category: Vulnerability category (optional)
        raw: Original data for extension fields
    """
    testcase: str
    cwe: str
    is_vulnerable: bool
    category: Optional[str] = None
    raw: dict = field(default_factory=dict)


@dataclass
class EvalResult:
    """Represents evaluation metrics for a tool on a specific CWE.

    Attributes:
        tool: Tool name
        cwe: CWE identifier
        tp: True positives
        fp: False positives
        fn: False negatives
        tn: True negatives (optional)
        precision: TP / (TP + FP)
        recall: TP / (TP + FN)
        f1: F1 score
        total_findings: Total number of findings (before deduplication)
        total_expected_vulnerable: Total vulnerable cases in ground truth
        total_expected_cases: Total cases in ground truth (optional)
        schema_version: Schema version identifier
    """
    tool: str
    cwe: str
    tp: int
    fp: int
    fn: int
    tn: Optional[int]
    precision: float
    recall: float
    f1: float
    total_findings: int
    total_expected_vulnerable: int
    total_expected_cases: Optional[int] = None
    schema_version: str = "vep.eval.v2"
