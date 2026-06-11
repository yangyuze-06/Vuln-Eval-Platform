"""VEP Evaluation: Unified evaluator for vulnerability findings.

Phase 2: Unified Evaluation Core
Core evaluation logic compatible with eval_codefuse_results.py.
"""

from typing import List

from vep.core.models import Finding, ExpectedCase, EvalResult


def evaluate_findings(
    findings: List[Finding],
    expected_cases: List[ExpectedCase],
    tool: str,
    cwe: str,
    include_tn: bool = True,
) -> EvalResult:
    """Evaluate findings against ground truth expected cases.

    Matching strategy:
        - Match by testcase identifier (deduplicate multiple findings per testcase)
        - TP: finding matches vulnerable expected case
        - FP: finding matches non-vulnerable expected case OR no expected case exists
        - FN: vulnerable expected case with no finding
        - TN: non-vulnerable expected case with no finding (if include_tn=True)

    Args:
        findings: List of Finding objects
        expected_cases: List of ExpectedCase objects
        tool: Tool name for result metadata
        cwe: CWE identifier for result metadata
        include_tn: Whether to calculate true negatives

    Returns:
        EvalResult with metrics

    Note:
        Follows eval_codefuse_results.py logic with "all_non_gt" FP mode:
        FP includes both in-scope negatives and out-of-scope findings.
    """
    # Deduplicate findings by testcase (keep first occurrence)
    testcase_to_finding = {}
    for finding in findings:
        if finding.testcase and finding.testcase not in testcase_to_finding:
            testcase_to_finding[finding.testcase] = finding

    detected_testcases = set(testcase_to_finding.keys())

    # Build ground truth sets
    vulnerable_cases = set()
    non_vulnerable_cases = set()
    all_expected_cases = set()

    for expected in expected_cases:
        all_expected_cases.add(expected.testcase)
        if expected.is_vulnerable:
            vulnerable_cases.add(expected.testcase)
        else:
            non_vulnerable_cases.add(expected.testcase)

    # Calculate sets
    tp_cases = detected_testcases & vulnerable_cases
    fp_in_scope_cases = detected_testcases & non_vulnerable_cases
    fp_out_scope_cases = detected_testcases - all_expected_cases
    fn_cases = vulnerable_cases - detected_testcases
    tn_cases = non_vulnerable_cases - detected_testcases

    # Metrics (following all_non_gt FP mode)
    tp = len(tp_cases)
    fp = len(fp_in_scope_cases) + len(fp_out_scope_cases)  # all_non_gt mode
    fn = len(fn_cases)
    tn = len(tn_cases) if include_tn else None

    # Calculate rates
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

    # Round to 4 decimal places (match old behavior)
    precision = round(precision, 4)
    recall = round(recall, 4)
    f1 = round(f1, 4)

    return EvalResult(
        tool=tool,
        cwe=cwe,
        tp=tp,
        fp=fp,
        fn=fn,
        tn=tn,
        precision=precision,
        recall=recall,
        f1=f1,
        total_findings=len(findings),
        total_expected_vulnerable=len(vulnerable_cases),
        total_expected_cases=len(all_expected_cases),
        schema_version="vep.eval.v2"
    )
