#!/usr/bin/env python3
"""
Run Phase 8 error analysis on the SROIE dataset.

Examples:
    python scripts/run_error_analysis.py --split train
    python scripts/run_error_analysis.py --split train --error-type subtotal_confusion
    python scripts/run_error_analysis.py --split train --show-examples --limit 10
    python scripts/run_error_analysis.py --split train --output error_report.json
    python scripts/run_error_analysis.py --split train --generate-report
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config import Config
from core.logging_config import get_logger
from pipeline.pipeline import DocumentProcessor
from tests.analysis.error_analysis import (
    ErrorAnalyzer,
    ErrorType,
    generate_confidence_vs_accuracy_plot,
    generate_error_distribution_chart,
)
from tests.metrics.evaluation import DocumentEvaluator

logger = get_logger(__name__)


def print_separator(char: str = "=", length: int = 80):
    """Print a separator."""
    print(char * length)


def print_header(title: str):
    """Print a section header."""
    print_separator()
    print(title)
    print_separator()


def format_pct(value: float) -> str:
    """Format as percentage."""
    return f"{value * 100:.1f}%"


def convert_error_records_for_analysis(error_records: List[Dict]) -> tuple[List[Dict], List[Dict], List[str]]:
    """
    Convert evaluator field-level records into analyzer input lists.

    Groups two field-level records per image into one prediction record and one
    ground-truth record, plus OCR text list.
    """
    grouped = {}

    for record in error_records:
        image_id = record.get("image_id") or Path(record.get("image_path", "unknown")).stem
        if image_id not in grouped:
            grouped[image_id] = {
                "prediction": {"image_id": image_id},
                "ground_truth": {"image_id": image_id},
                "ocr_text": record.get("ocr_text", ""),
            }

        field_name = record["field_name"]
        grouped[image_id]["prediction"][field_name] = record.get("prediction")
        grouped[image_id]["prediction"][f"{field_name}_confidence"] = record.get("confidence", 0.0)
        grouped[image_id]["ground_truth"][field_name] = record.get("ground_truth")
        if record.get("ocr_text"):
            grouped[image_id]["ocr_text"] = record["ocr_text"]

    ordered = [grouped[key] for key in sorted(grouped.keys())]
    predictions = [item["prediction"] for item in ordered]
    ground_truth = [item["ground_truth"] for item in ordered]
    ocr_results = [item["ocr_text"] for item in ordered]
    return predictions, ground_truth, ocr_results


def print_summary(report: Dict):
    """Print high-level summary."""
    summary = report["summary"]
    print_header("=== ERROR ANALYSIS REPORT ===")
    print()
    print("Summary:")
    print(f"  Total Samples: {summary['total_samples']}")
    print(f"  Total Errors: {summary['total_errors']} ({summary['error_rate'] * 100:.1f}%)")
    print()
    print("  By Field:")
    print(f"    Date:  {summary['by_field']['date']['errors']} errors ({summary['by_field']['date']['error_rate'] * 100:.1f}%)")
    print(f"    Total: {summary['by_field']['total']['errors']} errors ({summary['by_field']['total']['error_rate'] * 100:.1f}%)")
    print()


def print_examples(report: Dict, error_type: str | None = None, limit: int = 5):
    """Print selected error examples."""
    categories = report["by_category"]
    selected_items = categories.items()

    if error_type:
        selected_items = [(error_type, categories.get(error_type, {}))]

    for category_name, payload in selected_items:
        if not payload:
            continue

        print(f"Top Examples - {category_name.replace('_', ' ').title()}:")
        for idx, example in enumerate(payload.get("examples", [])[:limit], start=1):
            print(
                f"  {idx}. {example['image_id']}: "
                f"Predicted {example['predicted']}, Actual {example['actual']} "
                f"(conf: {example['confidence']:.2f})"
            )
            print(f"     Explanation: {example['explanation']}")
        print()


def print_insights_and_recommendations(report: Dict):
    """Print insights and recommendations."""
    print("Key Insights:")
    for insight in report.get("insights", []):
        print(f"  ✓ {insight}")
    print()

    print("Recommendations:")
    for recommendation in report.get("recommendations", []):
        print(f"  → {recommendation}")
    print()


def _json_safe(value):
    """Convert nested objects into JSON-safe Python primitives."""
    if isinstance(value, dict):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def save_report(report: Dict, output_path: str):
    """Save JSON report."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as file_obj:
        json.dump(_json_safe(report), file_obj, indent=2, ensure_ascii=False)
    print(f"Saved report to {path}")


def save_html_report(report: Dict, output_path: str):
    """Save a lightweight HTML report."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    chart = generate_error_distribution_chart(report).replace("\n", "<br>")
    insights = "".join(f"<li>{item}</li>" for item in report.get("insights", []))
    recommendations = "".join(f"<li>{item}</li>" for item in report.get("recommendations", []))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Error Analysis Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 2rem; }}
pre {{ background: #f6f8fa; padding: 1rem; border-radius: 6px; }}
h1, h2 {{ color: #222; }}
</style>
</head>
<body>
<h1>Error Analysis Report</h1>
<h2>Summary</h2>
<pre>{json.dumps(_json_safe(report['summary']), indent=2)}</pre>
<h2>Error Distribution</h2>
<pre>{chart}</pre>
<h2>Insights</h2>
<ul>{insights}</ul>
<h2>Recommendations</h2>
<ul>{recommendations}</ul>
</body>
</html>
"""
    with open(path, "w", encoding="utf-8") as file_obj:
        file_obj.write(html)

    print(f"Saved HTML report to {path}")


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="Run error analysis on SROIE evaluation results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--split", choices=["train", "test"], default="train")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--error-type", type=str, default=None)
    parser.add_argument("--show-examples", action="store_true")
    parser.add_argument("--output", type=str, default=None)
    parser.add_argument("--generate-report", action="store_true")
    parser.add_argument("--no-cache", action="store_true")

    args = parser.parse_args()

    Config.ensure_directories()

    try:
        processor = DocumentProcessor(use_cache=not args.no_cache)
        evaluator = DocumentEvaluator(processor)
        analyzer = ErrorAnalyzer()

        print_header("RUNNING EVALUATION WITH ERROR TRACKING")
        evaluation_results, error_records = evaluator.evaluate_with_error_tracking(
            split=args.split,
            limit=args.limit,
        )

        predictions, ground_truth, ocr_results = convert_error_records_for_analysis(error_records)
        report = analyzer.analyze_errors(predictions, ground_truth, ocr_results)
        report["evaluation"] = evaluation_results

        print_summary(report)
        print(generate_error_distribution_chart(report))
        print()
        print(generate_confidence_vs_accuracy_plot(report.get("errors", [])[:80]))
        print()
        print_insights_and_recommendations(report)

        if args.show_examples or args.error_type:
            print_examples(report, error_type=args.error_type, limit=args.limit or 5)

        if args.output:
            save_report(report, args.output)

        if args.generate_report:
            html_output = args.output.replace(".json", ".html") if args.output else "output/error_report.html"
            save_html_report(report, html_output)

        print_separator()
        print("Error analysis complete")
        print_separator()
        return 0

    except KeyboardInterrupt:
        print("\nInterrupted by user")
        return 1
    except Exception as exc:
        logger.error(f"Error analysis failed: {exc}", exc_info=True)
        print(f"\nError analysis failed: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
