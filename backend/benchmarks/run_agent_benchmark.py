#!/usr/bin/env python3
"""
Agent Benchmark Runner

Evaluates Agent's ability to generate logically valid strategies from prompts.

Usage:
    python -m benchmarks.run_agent_benchmark
    python -m benchmarks.run_agent_benchmark --subset 5  # Run first 5 cases only
    python -m benchmarks.run_agent_benchmark --output results/agent_bench_YYYYMMDD.json
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.agent_prompt_test_set import AGENT_PROMPT_TEST_SET
from app.services.agent_service import generate_strategy_from_prompt


def evaluate_param_constraint(param_name: str, param_value: float | int, params: dict, constraint: str) -> bool:
    """
    Evaluate a parameter constraint expression.

    Args:
        param_name: Name of the parameter being checked
        param_value: Value of the parameter being checked
        params: Dictionary of all parameter values
        constraint: Expression like "< long_window" or "> short_window"

    Returns:
        True if constraint is satisfied
    """
    constraint = constraint.strip()

    for op, py_op in [("<=", "<="), (">=", ">="), ("<", "<"), (">", ">"), ("==", "==")]:
        if op in constraint:
            ref_param = constraint.replace(op, "").strip()
            if ref_param in params:
                ref_value = params[ref_param]
                # Handle both direct values and parameter definitions
                if isinstance(ref_value, dict):
                    ref_value = ref_value.get("default", ref_value.get("value"))

                # Evaluate: param_value op ref_value
                return eval(f"{param_value} {py_op} {ref_value}", {"__builtins__": {}})
    return True


def evaluate_quality_check(params: dict, check: str) -> tuple[bool, str]:
    """
    Evaluate a quality check expression.

    Args:
        params: Dictionary of parameter values
        check: Expression like "short_window < long_window"

    Returns:
        (passed, message)
    """
    try:
        # Extract parameter values
        local_vars = {}
        for key, value in params.items():
            # Handle both direct values and parameter definitions
            if isinstance(value, dict):
                local_vars[key] = value.get("default", value.get("value", 0))
            else:
                local_vars[key] = value

        # Evaluate the check
        result = eval(check, {"__builtins__": {}}, local_vars)
        return result, f"[PASS] {check}" if result else f"[FAIL] {check}"
    except Exception as e:
        return False, f"[FAIL] {check} (error: {e})"


def run_agent_benchmark(test_cases: list[dict], output_path: str | None = None) -> dict:
    """
    Run Agent benchmark evaluation.

    Args:
        test_cases: List of test cases from AGENT_PROMPT_TEST_SET
        output_path: Optional path to save results

    Returns:
        Dictionary with benchmark results
    """
    results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_cases": len(test_cases),
            "test_set": "AGENT_PROMPT_TEST_SET",
        },
        "cases": [],
        "summary": {
            "passed": 0,
            "failed": 0,
            "errors": 0,
        },
    }

    print(f"Running Agent Benchmark ({len(test_cases)} cases)...\n")

    for idx, test_case in enumerate(test_cases, 1):
        case_id = test_case["id"]
        prompt = test_case["prompt"]
        expected_type = test_case["expected_type"]
        expected_params = test_case.get("expected_params", {})
        quality_checks = test_case.get("quality_checks", [])

        print(f"[{idx}/{len(test_cases)}] {case_id}: {prompt[:60]}...")

        case_result = {
            "id": case_id,
            "category": test_case["category"],
            "prompt": prompt,
            "expected_type": expected_type,
            "status": "pending",
            "checks_passed": [],
            "checks_failed": [],
            "error": None,
        }

        try:
            # Generate strategy
            generated = generate_strategy_from_prompt(prompt)
            case_result["generated_type"] = generated.strategy_type
            case_result["generated_params"] = generated.parameters

            # Check 1: Strategy type matches
            type_match = generated.strategy_type == expected_type
            if type_match:
                case_result["checks_passed"].append(f"[PASS] Type: {generated.strategy_type}")
            else:
                case_result["checks_failed"].append(
                    f"[FAIL] Type mismatch: expected {expected_type}, got {generated.strategy_type}"
                )

            # Check 2: Expected parameters exist and match constraints
            params = generated.parameters
            for param_name, param_spec in expected_params.items():
                if param_name not in params:
                    case_result["checks_failed"].append(f"[FAIL] Missing parameter: {param_name}")
                    continue

                actual_value = params[param_name]
                # Handle both direct values and parameter definitions
                if isinstance(actual_value, dict):
                    actual_value = actual_value.get("default", actual_value.get("value"))

                # Check expected value (with tolerance)
                if "value" in param_spec:
                    expected_value = param_spec["value"]
                    tolerance = param_spec.get("tolerance", 0)
                    if abs(actual_value - expected_value) <= tolerance:
                        case_result["checks_passed"].append(
                            f"[PASS] {param_name}={actual_value} (expected {expected_value}+-{tolerance})"
                        )
                    else:
                        case_result["checks_failed"].append(
                            f"[FAIL] {param_name}={actual_value} (expected {expected_value}+-{tolerance})"
                        )

                # Check min/max bounds
                if "min" in param_spec and actual_value < param_spec["min"]:
                    case_result["checks_failed"].append(
                        f"[FAIL] {param_name}={actual_value} below min {param_spec['min']}"
                    )
                elif "max" in param_spec and actual_value > param_spec["max"]:
                    case_result["checks_failed"].append(
                        f"[FAIL] {param_name}={actual_value} above max {param_spec['max']}"
                    )
                else:
                    case_result["checks_passed"].append(f"[PASS] {param_name}={actual_value} in bounds")

                # Check constraint (e.g., "< long_window")
                if "constraint" in param_spec:
                    constraint_ok = evaluate_param_constraint(param_name, actual_value, params, param_spec["constraint"])
                    if constraint_ok:
                        case_result["checks_passed"].append(
                            f"[PASS] {param_name} satisfies {param_spec['constraint']}"
                        )
                    else:
                        case_result["checks_failed"].append(
                            f"[FAIL] {param_name} violates {param_spec['constraint']}"
                        )

            # Check 3: Quality checks (logical constraints)
            for check in quality_checks:
                passed, message = evaluate_quality_check(params, check)
                if passed:
                    case_result["checks_passed"].append(message)
                else:
                    case_result["checks_failed"].append(message)

            # Determine overall status
            if len(case_result["checks_failed"]) == 0:
                case_result["status"] = "PASS"
                results["summary"]["passed"] += 1
                print(f"  [PASS] ({len(case_result['checks_passed'])} checks)")
            else:
                case_result["status"] = "FAIL"
                results["summary"]["failed"] += 1
                print(f"  [FAIL] ({len(case_result['checks_failed'])} failed checks)")
                for failed_check in case_result["checks_failed"]:
                    print(f"    {failed_check}")

        except Exception as e:
            case_result["status"] = "ERROR"
            case_result["error"] = str(e)
            results["summary"]["errors"] += 1
            print(f"  [ERROR]: {e}")

        results["cases"].append(case_result)

    # Calculate pass rate
    total = len(test_cases)
    passed = results["summary"]["passed"]
    results["summary"]["pass_rate"] = passed / total if total > 0 else 0

    # Save results if output path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n[OK] Results saved to {output_path}")

    # Print summary
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    print(f"Total cases: {total}")
    print(f"Passed: {passed} ({results['summary']['pass_rate']:.1%})")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Errors: {results['summary']['errors']}")
    print("=" * 60)

    return results


def main():
    parser = argparse.ArgumentParser(description="Run Agent benchmark evaluation")
    parser.add_argument("--subset", type=int, help="Run only first N test cases")
    parser.add_argument("--output", type=str, help="Output file path for results")
    parser.add_argument("--category", type=str, help="Filter by category (e.g., moving_average)")

    args = parser.parse_args()

    # Load test cases
    test_cases = AGENT_PROMPT_TEST_SET

    # Filter by category if specified
    if args.category:
        test_cases = [tc for tc in test_cases if tc["category"] == args.category]
        print(f"Filtered to category '{args.category}': {len(test_cases)} cases")

    # Limit to subset if specified
    if args.subset:
        test_cases = test_cases[: args.subset]
        print(f"Running subset: first {len(test_cases)} cases")

    # Generate default output path if not provided
    output_path = args.output
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f".runtime/benchmarks/agent_benchmark_{timestamp}.json"

    # Run benchmark
    results = run_agent_benchmark(test_cases, output_path=output_path)

    # Exit with error code if there are failures
    if results["summary"]["failed"] > 0 or results["summary"]["errors"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
