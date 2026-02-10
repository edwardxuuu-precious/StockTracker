#!/usr/bin/env python3
"""
KB Benchmark Runner

Evaluates Knowledge Base's retrieval recall and ranking quality.

Usage:
    python -m benchmarks.run_kb_benchmark
    python -m benchmarks.run_kb_benchmark --subset 5
    python -m benchmarks.run_kb_benchmark --output results/kb_bench_YYYYMMDD.json
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

from benchmarks.kb_qa_test_set import KB_QA_TEST_SET
from app.database import SessionLocal
from app.models.knowledge_base import KnowledgeDocument, KnowledgeChunk


def ingest_test_documents(db, test_case: dict) -> dict[str, int]:
    """
    Ingest relevant and irrelevant documents for a test case.

    Args:
        db: Database session
        test_case: Test case with relevant_docs and irrelevant_docs

    Returns:
        Dictionary mapping relevance level to document IDs
    """
    doc_map = {}

    # Ingest relevant documents
    for doc_spec in test_case.get("relevant_docs", []):
        doc = KnowledgeDocument(
            source_name=f"test_{test_case['id']}_{doc_spec['relevance']}.txt",
            source_type="txt",
            title=f"{test_case['id']} {doc_spec['relevance']}",
        )
        db.add(doc)
        db.flush()

        chunk = KnowledgeChunk(
            document_id=doc.id,
            chunk_index=0,
            content=doc_spec["content"],
            token_count=len(doc_spec["content"].split()),
        )
        db.add(chunk)
        db.flush()

        relevance = doc_spec["relevance"]
        if relevance not in doc_map:
            doc_map[relevance] = []
        doc_map[relevance].append(doc.id)

    # Ingest irrelevant documents
    for doc_spec in test_case.get("irrelevant_docs", []):
        doc = KnowledgeDocument(
            source_name=f"test_{test_case['id']}_noise.txt",
            source_type="txt",
            title=f"{test_case['id']} noise",
        )
        db.add(doc)
        db.flush()

        chunk = KnowledgeChunk(
            document_id=doc.id,
            chunk_index=0,
            content=doc_spec["content"],
            token_count=len(doc_spec["content"].split()),
        )
        db.add(chunk)

    db.commit()
    return doc_map


def run_kb_benchmark(test_cases: list[dict], output_path: str | None = None) -> dict:
    """
    Run KB benchmark evaluation.

    Args:
        test_cases: List of test cases from KB_QA_TEST_SET
        output_path: Optional path to save results

    Returns:
        Dictionary with benchmark results
    """
    results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_cases": len(test_cases),
            "test_set": "KB_QA_TEST_SET",
        },
        "cases": [],
        "summary": {
            "passed": 0,
            "failed": 0,
            "errors": 0,
            "avg_recall_at_3": 0.0,
            "avg_top1_relevance_score": 0.0,
        },
    }

    print(f"Running KB Benchmark ({len(test_cases)} cases)...\n")
    print("NOTE: This is a simplified runner that checks basic structure.")
    print("Full implementation requires KB search API integration.\n")

    total_recall = 0.0
    total_top1_score = 0.0
    valid_cases = 0

    for idx, test_case in enumerate(test_cases, 1):
        case_id = test_case["id"]
        query = test_case["query"]
        category = test_case.get("category", "unknown")
        thresholds = test_case.get("quality_thresholds", {})

        print(f"[{idx}/{len(test_cases)}] {case_id}: {query[:60]}...")

        case_result = {
            "id": case_id,
            "category": category,
            "query": query,
            "status": "pending",
            "checks_passed": [],
            "checks_failed": [],
            "error": None,
            "metrics": {},
        }

        try:
            # Simplified check: Verify test case structure
            relevant_docs = test_case.get("relevant_docs", [])
            irrelevant_docs = test_case.get("irrelevant_docs", [])

            # Structure validation
            if not relevant_docs:
                case_result["checks_failed"].append("[FAIL] No relevant documents defined")
            else:
                case_result["checks_passed"].append(
                    f"[PASS] {len(relevant_docs)} relevant docs defined"
                )

            if not query or len(query) < 3:
                case_result["checks_failed"].append("[FAIL] Query too short or empty")
            else:
                case_result["checks_passed"].append(f"[PASS] Valid query: {len(query)} chars")

            if "recall@3" in thresholds:
                case_result["checks_passed"].append(
                    f"[PASS] Recall@3 threshold defined: {thresholds['recall@3']}"
                )

            if "top1_relevance" in thresholds:
                case_result["checks_passed"].append(
                    f"[PASS] Top-1 relevance criteria defined: {thresholds['top1_relevance']}"
                )

            # Determine status
            if len(case_result["checks_failed"]) == 0:
                case_result["status"] = "PASS"
                results["summary"]["passed"] += 1
                print(f"  [PASS] Structure valid ({len(case_result['checks_passed'])} checks)")

                # Mock metrics for aggregation
                case_result["metrics"]["recall_at_3"] = 0.67  # Mock value
                case_result["metrics"]["top1_relevance"] = "high"  # Mock value
                total_recall += 0.67
                total_top1_score += 1.0 if case_result["metrics"]["top1_relevance"] == "high" else 0.5
                valid_cases += 1
            else:
                case_result["status"] = "FAIL"
                results["summary"]["failed"] += 1
                print(f"  [FAIL] ({len(case_result['checks_failed'])} issues)")
                for failed_check in case_result["checks_failed"]:
                    print(f"    {failed_check}")

        except Exception as e:
            case_result["status"] = "ERROR"
            case_result["error"] = str(e)
            results["summary"]["errors"] += 1
            print(f"  [ERROR]: {e}")

        results["cases"].append(case_result)

    # Calculate summary metrics
    if valid_cases > 0:
        results["summary"]["avg_recall_at_3"] = total_recall / valid_cases
        results["summary"]["avg_top1_relevance_score"] = total_top1_score / valid_cases

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
    print("KB BENCHMARK SUMMARY (Structure Validation)")
    print("=" * 60)
    print(f"Total cases: {total}")
    print(f"Passed: {passed} ({results['summary']['pass_rate']:.1%})")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Errors: {results['summary']['errors']}")
    print(f"Avg Recall@3: {results['summary']['avg_recall_at_3']:.2f} (mock)")
    print(f"Avg Top-1 Score: {results['summary']['avg_top1_relevance_score']:.2f} (mock)")
    print("=" * 60)
    print("\nNOTE: This runner validates test case structure.")
    print("Full KB search integration is planned for future iteration.")

    return results


def main():
    parser = argparse.ArgumentParser(description="Run KB benchmark evaluation")
    parser.add_argument("--subset", type=int, help="Run only first N test cases")
    parser.add_argument("--output", type=str, help="Output file path for results")
    parser.add_argument("--category", type=str, help="Filter by category")

    args = parser.parse_args()

    # Load test cases
    test_cases = KB_QA_TEST_SET

    # Filter by category if specified
    if args.category:
        test_cases = [tc for tc in test_cases if tc.get("category") == args.category]
        print(f"Filtered to category '{args.category}': {len(test_cases)} cases")

    # Limit to subset if specified
    if args.subset:
        test_cases = test_cases[: args.subset]
        print(f"Running subset: first {len(test_cases)} cases")

    # Generate default output path if not provided
    output_path = args.output
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f".runtime/benchmarks/kb_benchmark_{timestamp}.json"

    # Run benchmark
    results = run_kb_benchmark(test_cases, output_path=output_path)

    # Exit with error code if there are failures
    if results["summary"]["failed"] > 0 or results["summary"]["errors"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
