"""
Unit tests for Phase 8 error analysis.
"""

from tests.analysis.error_analysis import (
    ErrorAnalyzer,
    ErrorCategorizer,
    ErrorType,
    FailurePatternDetector,
    generate_confidence_vs_accuracy_plot,
    generate_error_distribution_chart,
)


def test_categorize_missing_field():
    categorizer = ErrorCategorizer()

    error_type = categorizer.categorize_error(
        prediction=None,
        ground_truth="2018-03-30",
        confidence=0.9,
        ocr_text="Date: 30/03/2018",
        field_name="date",
    )

    assert error_type == ErrorType.MISSING_FIELD


def test_categorize_low_confidence_error():
    categorizer = ErrorCategorizer()

    error_type = categorizer.categorize_error(
        prediction="2018-03-29",
        ground_truth="2018-03-30",
        confidence=0.2,
        ocr_text="Date : 30/03/2018",
        field_name="date",
    )

    assert error_type == ErrorType.LOW_CONFIDENCE


def test_detect_subtotal_confusion():
    categorizer = ErrorCategorizer()

    error_type = categorizer.categorize_error(
        prediction=45.50,
        ground_truth=52.30,
        confidence=0.82,
        ocr_text=(
            "Subtotal 45.50\n"
            "Tax 6.80\n"
            "Total 52.30\n"
        ),
        field_name="total",
    )

    assert error_type == ErrorType.SUBTOTAL_CONFUSION


def test_detect_date_parsing_error():
    categorizer = ErrorCategorizer()

    error_type = categorizer.categorize_error(
        prediction="32/13/2018",
        ground_truth="2018-03-30",
        confidence=0.88,
        ocr_text="Date: 32/13/2018",
        field_name="date",
    )

    assert error_type == ErrorType.DATE_PARSING_ERROR


def test_detect_ocr_noise():
    categorizer = ErrorCategorizer()

    error_type = categorizer.categorize_error(
        prediction="2O18-O3-3O",
        ground_truth="2018-03-30",
        confidence=0.9,
        ocr_text="D@te ~~ 2O18-O3-3O",
        field_name="date",
    )

    assert error_type == ErrorType.OCR_NOISE


def test_failure_pattern_detector_confusions():
    detector = FailurePatternDetector()

    errors = [
        {
            "predicted": "2O18-O3-3O",
            "actual": "2018-03-30",
        },
        {
            "predicted": "INV-I23",
            "actual": "INV-123",
        },
        {
            "predicted": "5.20",
            "actual": "S.20",
        },
    ]

    patterns = detector.detect_ocr_confusion_patterns(errors)

    assert any(pair[0] == "0" and pair[1] == "O" for pair in patterns)
    assert any(pair[0] == "1" and pair[1] == "I" for pair in patterns)


def test_error_analyzer_generates_summary_and_examples():
    analyzer = ErrorAnalyzer()

    predictions = [
        {
            "image_id": "X1",
            "date": "2018-03-29",
            "date_confidence": 0.92,
            "total": 45.50,
            "total_confidence": 0.81,
        },
        {
            "image_id": "X2",
            "date": None,
            "date_confidence": 0.0,
            "total": 10.00,
            "total_confidence": 0.45,
        },
    ]

    ground_truth = [
        {
            "image_id": "X1",
            "date": "2018-03-30",
            "total": 52.30,
        },
        {
            "image_id": "X2",
            "date": "2018-04-01",
            "total": 10.50,
        },
    ]

    ocr_results = [
        "Subtotal 45.50 Tax 6.80 Total 52.30 Date 30/03/2018",
        "Date 01/04/2018 Total 10.50",
    ]

    report = analyzer.analyze_errors(predictions, ground_truth, ocr_results)

    assert report["summary"]["total_samples"] == 2
    assert report["summary"]["total_errors"] >= 3
    assert "by_category" in report
    assert "insights" in report
    assert "recommendations" in report
    assert any(category in report["by_category"] for category in ["subtotal_confusion", "missing_field", "low_confidence"])


def test_get_error_examples_filters_category():
    analyzer = ErrorAnalyzer()

    predictions = [
        {
            "image_id": "X1",
            "date": "2018-03-30",
            "date_confidence": 0.95,
            "total": 45.50,
            "total_confidence": 0.83,
        }
    ]
    ground_truth = [
        {
            "image_id": "X1",
            "date": "2018-03-30",
            "total": 52.30,
        }
    ]
    ocr_results = ["Subtotal 45.50 Tax 6.80 Total 52.30"]

    examples = analyzer.get_error_examples(
        ErrorType.SUBTOTAL_CONFUSION,
        predictions,
        ground_truth,
        ocr_results,
        limit=3,
    )

    assert len(examples) == 1
    assert examples[0]["image_id"] == "X1"


def test_generate_insights_handles_empty_distribution():
    analyzer = ErrorAnalyzer()

    insights = analyzer.generate_insights({}, {}, total_errors=0)

    assert insights == ["No errors detected in the evaluated sample set"]


def test_generate_error_distribution_chart():
    chart = generate_error_distribution_chart(
        {
            "by_category": {
                "subtotal_confusion": {"count": 10, "percentage": 50.0},
                "ocr_noise": {"count": 5, "percentage": 25.0},
            }
        }
    )

    assert "Subtotal Confusion" in chart
    assert "OCR Noise" in chart


def test_generate_confidence_vs_accuracy_plot():
    plot = generate_confidence_vs_accuracy_plot(
        [
            {"confidence": 0.1, "is_error": True},
            {"confidence": 0.9, "is_error": False},
        ]
    )

    assert "Confidence vs Accuracy" in plot
    assert "x=confidence" in plot


def test_analyze_errors_handles_edge_cases():
    analyzer = ErrorAnalyzer()

    report = analyzer.analyze_errors([], [], [])

    assert report["summary"]["total_samples"] == 0
    assert report["summary"]["total_errors"] == 0
    assert report["recommendations"]

# Made with Bob
