"""
Error Analysis Module for Adaptive Document Intelligence System.

This module provides deterministic error categorization and dataset-level
failure analysis for the SROIE receipt extraction pipeline.

It focuses on understanding failure modes rather than fixing them:
- Categorizing incorrect predictions into actionable error types
- Detecting recurring OCR and extraction failure patterns
- Generating examples, insights, and recommendations
- Providing lightweight ASCII visualizations for CLI usage
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from tests.data.sroie_loader import normalize_date, normalize_total


class ErrorType(Enum):
    """Error type categories."""

    WRONG_TOTAL = "wrong_total"
    SUBTOTAL_CONFUSION = "subtotal_confusion"
    DATE_PARSING_ERROR = "date_parsing_error"
    DATE_FORMAT_ERROR = "date_format_error"
    OCR_NOISE = "ocr_noise"
    MISSING_FIELD = "missing_field"
    EXTRACTION_FAILURE = "extraction_failure"
    LOW_CONFIDENCE = "low_confidence"
    OTHER = "other"


@dataclass
class ErrorContext:
    """Structured representation of a single field-level error."""

    image_id: str
    field_name: str
    predicted: Any
    actual: Any
    confidence: float
    ocr_text: str
    error_type: ErrorType
    explanation: str
    ocr_quality: float
    is_error: bool = True


class ErrorCategorizer:
    """
    Categorize prediction errors into specific types.

    Analyzes why predictions failed and assigns categories using deterministic
    heuristics suitable for receipt date and total extraction.
    """

    LOW_CONFIDENCE_THRESHOLD = 0.5
    OCR_NOISE_CHARS = {"|", "~", "`", "_", "=", "«", "»", "�"}

    def __init__(self):
        """Initialize categorizer."""
        self.total_keywords = [
            "total",
            "amount due",
            "grand total",
            "nett total",
            "net total",
            "balance due",
            "total due",
            "jumlah",
            "amt due",
        ]
        self.subtotal_keywords = [
            "subtotal",
            "sub total",
            "sub-total",
            "total before tax",
            "before tax",
            "gross",
            "pre-tax",
            "pretax",
            "nett",
            "nett sales",
            "sales amount",
        ]
        self.tax_keywords = ["tax", "gst", "vat", "service tax", "svc tax", "sst"]
        self.discount_keywords = ["discount", "disc", "rounding", "round off", "rebate"]

    def categorize_error(
        self,
        prediction: Any,
        ground_truth: Any,
        confidence: float,
        ocr_text: str,
        field_name: str
    ) -> ErrorType:
        """
        Categorize a single error.

        Args:
            prediction: Predicted value
            ground_truth: Actual value
            confidence: Prediction confidence
            ocr_text: Raw OCR text
            field_name: Field being analyzed

        Returns:
            ErrorType enum value
        """
        if self._is_missing(prediction):
            return ErrorType.MISSING_FIELD

        if confidence < self.LOW_CONFIDENCE_THRESHOLD:
            if self._contains_ocr_noise(ocr_text):
                return ErrorType.OCR_NOISE
            return ErrorType.LOW_CONFIDENCE

        if field_name == "total":
            return self.analyze_total_error(prediction, ground_truth, ocr_text)

        if field_name == "date":
            return self.analyze_date_error(prediction, ground_truth, ocr_text)

        if self._contains_ocr_noise(ocr_text):
            return ErrorType.OCR_NOISE

        return ErrorType.OTHER

    def analyze_total_error(
        self,
        prediction: float,
        ground_truth: float,
        ocr_text: str
    ) -> ErrorType:
        """
        Analyze why total extraction failed.

        Checks for:
        - Subtotal confusion (predicted value is subtotal)
        - Tax/discount confusion
        - OCR misread
        - Missing total in text
        """
        pred_val = self._safe_float(prediction)
        truth_val = self._safe_float(ground_truth)

        if pred_val is None or truth_val is None:
            return ErrorType.EXTRACTION_FAILURE

        if self._looks_like_subtotal(pred_val, truth_val, ocr_text):
            return ErrorType.SUBTOTAL_CONFUSION

        if not self._text_contains_currency_number(ocr_text, truth_val):
            if self._contains_ocr_noise(ocr_text):
                return ErrorType.OCR_NOISE
            return ErrorType.EXTRACTION_FAILURE

        if self._contains_ocr_noise(ocr_text):
            return ErrorType.OCR_NOISE

        return ErrorType.WRONG_TOTAL

    def analyze_date_error(
        self,
        prediction: str,
        ground_truth: str,
        ocr_text: str
    ) -> ErrorType:
        """
        Analyze why date extraction failed.

        Checks for:
        - Format parsing issues
        - OCR misread (0/O, 1/I confusion)
        - Missing date in text
        - Wrong date selected
        """
        pred_str = "" if prediction is None else str(prediction).strip()
        truth_str = "" if ground_truth is None else str(ground_truth).strip()

        if not pred_str:
            return ErrorType.MISSING_FIELD

        normalized_pred = normalize_date(pred_str)
        normalized_truth = normalize_date(truth_str) or truth_str

        if normalized_pred is None:
            if self._contains_ocr_confusion(pred_str) or self._contains_ocr_noise(ocr_text):
                return ErrorType.OCR_NOISE
            return ErrorType.DATE_PARSING_ERROR

        if normalized_pred != normalized_truth:
            if self._contains_ocr_confusion(pred_str) or self._contains_ocr_noise(ocr_text):
                return ErrorType.OCR_NOISE

            if self._same_date_tokens_different_format(pred_str, truth_str):
                return ErrorType.DATE_FORMAT_ERROR

            if not self._text_contains_date_like(ocr_text):
                return ErrorType.EXTRACTION_FAILURE

            return ErrorType.DATE_FORMAT_ERROR

        return ErrorType.OTHER

    def explain_error(
        self,
        error_type: ErrorType,
        prediction: Any,
        ground_truth: Any,
        field_name: str,
        ocr_text: str
    ) -> str:
        """Generate concise explanation for an error type."""
        if error_type == ErrorType.SUBTOTAL_CONFUSION:
            return "Extracted subtotal or pre-tax amount instead of final total"
        if error_type == ErrorType.WRONG_TOTAL:
            return "Extracted numeric amount does not match the final total"
        if error_type == ErrorType.DATE_PARSING_ERROR:
            return "Detected date-like text but failed to parse it into normalized format"
        if error_type == ErrorType.DATE_FORMAT_ERROR:
            return "Selected or normalized an incorrect date format/value"
        if error_type == ErrorType.OCR_NOISE:
            return "OCR noise or character confusion likely corrupted extraction"
        if error_type == ErrorType.MISSING_FIELD:
            return f"No {field_name} value was extracted"
        if error_type == ErrorType.EXTRACTION_FAILURE:
            return f"Could not reliably locate the {field_name} in OCR text"
        if error_type == ErrorType.LOW_CONFIDENCE:
            return f"Prediction confidence too low for reliable {field_name} extraction"
        return f"Unclassified {field_name} extraction error"

    def estimate_ocr_quality(self, ocr_text: str) -> float:
        """Estimate OCR text quality using simple deterministic heuristics."""
        if not ocr_text:
            return 0.0

        length = len(ocr_text)
        alnum_ratio = sum(ch.isalnum() or ch.isspace() for ch in ocr_text) / max(length, 1)
        noise_ratio = sum(ch in self.OCR_NOISE_CHARS for ch in ocr_text) / max(length, 1)
        repeated_symbol_penalty = min(
            0.3,
            len(re.findall(r"[^A-Za-z0-9\s]{3,}", ocr_text)) * 0.05
        )
        quality = alnum_ratio - noise_ratio - repeated_symbol_penalty
        return max(0.0, min(1.0, quality))

    def _looks_like_subtotal(self, prediction: float, ground_truth: float, ocr_text: str) -> bool:
        """Check if predicted amount resembles a subtotal rather than final total."""
        text = (ocr_text or "").lower()
        if abs(prediction - ground_truth) < 0.01:
            return False

        subtotal_match = self._text_contains_currency_number_near_keywords(
            text, prediction, self.subtotal_keywords
        )
        total_match = self._text_contains_currency_number_near_keywords(
            text, ground_truth, self.total_keywords
        )
        has_tax_or_discount = any(keyword in text for keyword in self.tax_keywords + self.discount_keywords)

        if subtotal_match and total_match:
            return True

        if prediction < ground_truth and has_tax_or_discount and subtotal_match:
            return True

        difference = ground_truth - prediction
        if difference > 0 and difference / max(ground_truth, 0.01) <= 0.25 and subtotal_match:
            return True

        return False

    def _text_contains_currency_number(self, text: str, value: float, tolerance: float = 0.01) -> bool:
        """Check whether OCR text contains a numeric value close to the given amount."""
        target = self._safe_float(value)
        if target is None or not text:
            return False

        for number in self._extract_numbers(text):
            if abs(number - target) <= tolerance:
                return True
        return False

    def _text_contains_currency_number_near_keywords(
        self,
        text: str,
        value: float,
        keywords: List[str],
        window: int = 80
    ) -> bool:
        """Check whether a value occurs near indicative keywords."""
        if not text:
            return False

        normalized = text.lower()
        value_candidates = self._format_amount_candidates(value)

        for keyword in keywords:
            for match in re.finditer(re.escape(keyword.lower()), normalized):
                start = max(0, match.start() - window)
                end = min(len(normalized), match.end() + window)
                snippet = normalized[start:end]
                if any(candidate in snippet for candidate in value_candidates):
                    return True
                for number in self._extract_numbers(snippet):
                    if abs(number - float(value)) <= 0.01:
                        return True
        return False

    def _format_amount_candidates(self, value: float) -> List[str]:
        """Generate textual candidates for a float amount."""
        return [
            f"{value:.2f}",
            f"{value:.1f}",
            str(int(value)) if float(value).is_integer() else "",
            f"{value:,.2f}",
        ]

    def _extract_numbers(self, text: str) -> List[float]:
        """Extract float-like numbers from OCR text."""
        values = []
        for match in re.findall(r"\d[\d,]*\.?\d*", text or ""):
            parsed = normalize_total(match)
            if parsed is not None:
                values.append(parsed)
        return values

    def _contains_ocr_noise(self, text: str) -> bool:
        """Detect likely OCR noise from text characteristics."""
        if not text:
            return True

        if any(ch in text for ch in self.OCR_NOISE_CHARS):
            return True

        if re.search(r"[A-Za-z0-9]{1}[^A-Za-z0-9\s]{1,2}[A-Za-z0-9]{1}[^A-Za-z0-9\s]{1,2}[A-Za-z0-9]{1}", text):
            return True

        if len(re.findall(r"[^\w\s]{3,}", text)) > 0:
            return True

        return False

    def _contains_ocr_confusion(self, text: str) -> bool:
        """Detect common OCR-confused characters inside date strings."""
        if not text:
            return False
        return bool(re.search(r"[OIolSBZ]", text))

    def _same_date_tokens_different_format(self, prediction: str, truth: str) -> bool:
        """Check whether date strings share most digits but differ in formatting/order."""
        pred_digits = re.findall(r"\d+", prediction or "")
        truth_digits = re.findall(r"\d+", truth or "")
        if not pred_digits or not truth_digits:
            return False

        pred_flat = "".join(pred_digits)
        truth_flat = "".join(truth_digits)
        ratio = SequenceMatcher(None, pred_flat, truth_flat).ratio()
        return ratio >= 0.6 and prediction != truth

    def _text_contains_date_like(self, text: str) -> bool:
        """Check if OCR text contains any date-like pattern."""
        if not text:
            return False
        patterns = [
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
            r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",
            r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}\b",
            r"\b[A-Za-z]{3,9}\s+\d{1,2},\s*\d{2,4}\b",
        ]
        return any(re.search(pattern, text) for pattern in patterns)

    def _is_missing(self, value: Any) -> bool:
        """Check whether a predicted value is effectively missing."""
        return value is None or (isinstance(value, str) and not value.strip())

    def _safe_float(self, value: Any) -> Optional[float]:
        """Convert a value to float if possible."""
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None


class FailurePatternDetector:
    """
    Detect systematic failure patterns.

    Identifies recurring issues across the dataset.
    """

    LOW_QUALITY_THRESHOLD = 0.75
    LOW_CONF_THRESHOLD = 0.5

    def detect_patterns(
        self,
        errors: List[Dict]
    ) -> Dict:
        """
        Detect failure patterns.

        Returns:
            {
                'ocr_quality_correlation': {
                    'low_quality_error_rate': float,
                    'high_quality_error_rate': float
                },
                'confidence_correlation': {
                    'low_conf_error_rate': float,
                    'high_conf_error_rate': float
                },
                'field_specific': {
                    'date': {
                        'common_formats_failed': List[str],
                        'ocr_confusion_pairs': List[Tuple]
                    },
                    'total': {
                        'subtotal_rate': float,
                        'position_bias_issues': bool
                    }
                },
                'systematic_issues': List[str]
            }
        """
        low_quality = [e for e in errors if e.get("ocr_quality", 1.0) < self.LOW_QUALITY_THRESHOLD]
        high_quality = [e for e in errors if e.get("ocr_quality", 1.0) >= self.LOW_QUALITY_THRESHOLD]
        low_conf = [e for e in errors if e.get("confidence", 1.0) < self.LOW_CONF_THRESHOLD]
        high_conf = [e for e in errors if e.get("confidence", 1.0) >= self.LOW_CONF_THRESHOLD]

        subtotal_count = sum(
            1 for e in errors if e.get("error_type") == ErrorType.SUBTOTAL_CONFUSION.value
        )
        total_errors = sum(1 for e in errors if e.get("field_name") == "total")
        date_errors = [e for e in errors if e.get("field_name") == "date"]

        failed_formats = Counter(self._detect_failed_date_format(e) for e in date_errors)
        failed_formats.pop("unknown", None)

        confusion_pairs = self.detect_ocr_confusion_patterns(errors)

        position_bias_issues = subtotal_count > 0 and any(
            "bottom" in (e.get("explanation") or "").lower() or "final total" in (e.get("explanation") or "").lower()
            for e in errors
        )

        systematic_issues = []
        if len(low_quality) > len(high_quality):
            systematic_issues.append("A large share of failures occurs on low-quality OCR text")
        if len(low_conf) > 0:
            systematic_issues.append("Low-confidence predictions contribute materially to total error volume")
        if subtotal_count and total_errors and subtotal_count / total_errors >= 0.25:
            systematic_issues.append("Subtotal confusion is a major systematic issue for total extraction")
        if failed_formats:
            systematic_issues.append("Date failures are concentrated in specific input formats")

        return {
            "ocr_quality_correlation": {
                "low_quality_error_rate": len(low_quality) / len(errors) if errors else 0.0,
                "high_quality_error_rate": len(high_quality) / len(errors) if errors else 0.0,
            },
            "confidence_correlation": {
                "low_conf_error_rate": len(low_conf) / len(errors) if errors else 0.0,
                "high_conf_error_rate": len(high_conf) / len(errors) if errors else 0.0,
            },
            "field_specific": {
                "date": {
                    "common_formats_failed": [fmt for fmt, _ in failed_formats.most_common(5)],
                    "ocr_confusion_pairs": confusion_pairs[:5],
                },
                "total": {
                    "subtotal_rate": subtotal_count / total_errors if total_errors else 0.0,
                    "position_bias_issues": position_bias_issues,
                },
            },
            "systematic_issues": systematic_issues,
        }

    def detect_ocr_confusion_patterns(
        self,
        errors: List[Dict]
    ) -> List[Tuple[str, str, int]]:
        """
        Detect common OCR character confusions.

        Returns:
            [
                ('0', 'O', 15),
                ('1', 'I', 8),
                ...
            ]
        """
        candidate_pairs = [
            ("0", "O"),
            ("1", "I"),
            ("1", "l"),
            ("5", "S"),
            ("2", "Z"),
            ("8", "B"),
            ("6", "G"),
        ]
        counts = Counter()

        for error in errors:
            predicted = "" if error.get("predicted") is None else str(error.get("predicted"))
            actual = "" if error.get("actual") is None else str(error.get("actual"))
            for a, b in candidate_pairs:
                if (a in predicted and b in actual) or (b in predicted and a in actual):
                    counts[(a, b)] += 1

        return [(a, b, count) for (a, b), count in counts.most_common()]

    def _detect_failed_date_format(self, error: Dict) -> str:
        """Infer failed date format family from actual value."""
        actual = "" if error.get("actual") is None else str(error.get("actual"))
        raw = "" if error.get("ocr_text") is None else str(error.get("ocr_text"))

        if re.search(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", raw):
            return "DD/MM/YYYY"
        if re.search(r"\b\d{1,2}-\d{1,2}-\d{2,4}\b", raw):
            return "DD-MM-YYYY"
        if re.search(r"\b\d{4}-\d{1,2}-\d{1,2}\b", raw) or re.search(r"\b\d{4}/\d{1,2}/\d{1,2}\b", raw):
            return "YYYY-MM-DD"
        if re.search(r"\b[A-Za-z]{3,9}\s+\d{1,2},\s*\d{2,4}\b", raw) or re.search(
            r"\b\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}\b", raw
        ):
            return "TEXTUAL_MONTH"
        if actual:
            return "normalized_iso_target"
        return "unknown"


class ErrorAnalyzer:
    """
    Analyze errors across the dataset.

    Provides statistical insights and examples.
    """

    def __init__(self):
        """Initialize analyzer."""
        self.categorizer = ErrorCategorizer()
        self.pattern_detector = FailurePatternDetector()

    def analyze_errors(
        self,
        predictions: List[Dict],
        ground_truth: List[Dict],
        ocr_results: List[str]
    ) -> Dict:
        """
        Analyze all errors in predictions.

        Returns:
            structured error analysis dictionary
        """
        error_records = []
        total_samples = len(predictions)
        field_totals = {"date": 0, "total": 0}
        field_errors = {"date": 0, "total": 0}

        for prediction_record, truth_record, ocr_text in zip(predictions, ground_truth, ocr_results):
            image_id = (
                prediction_record.get("image_id")
                or truth_record.get("image_id")
                or f"sample_{len(error_records)}"
            )

            for field_name in ["date", "total"]:
                field_totals[field_name] += 1
                predicted = prediction_record.get(field_name)
                actual = truth_record.get(field_name)
                confidence = float(prediction_record.get(f"{field_name}_confidence", 0.0) or 0.0)

                if self._values_match(predicted, actual, field_name):
                    continue

                field_errors[field_name] += 1
                error_type = self.categorizer.categorize_error(
                    prediction=predicted,
                    ground_truth=actual,
                    confidence=confidence,
                    ocr_text=ocr_text,
                    field_name=field_name,
                )
                explanation = self.categorizer.explain_error(
                    error_type, predicted, actual, field_name, ocr_text
                )

                error_records.append({
                    "image_id": image_id,
                    "field_name": field_name,
                    "predicted": predicted,
                    "actual": actual,
                    "confidence": confidence,
                    "ocr_text": ocr_text,
                    "ocr_snippet": self._make_ocr_snippet(ocr_text, predicted, actual),
                    "error_type": error_type.value,
                    "explanation": explanation,
                    "ocr_quality": self.categorizer.estimate_ocr_quality(ocr_text),
                })

        total_errors = len(error_records)
        by_category = self._build_category_summary(error_records)
        patterns = self.pattern_detector.detect_patterns(error_records)
        insights = self.generate_insights(by_category, patterns, total_errors)
        recommendations = self.generate_recommendations(by_category, patterns)

        return {
            "summary": {
                "total_samples": total_samples,
                "total_errors": total_errors,
                "error_rate": total_errors / (total_samples * 2) if total_samples else 0.0,
                "by_field": {
                    "date": {
                        "total": field_totals["date"],
                        "errors": field_errors["date"],
                        "error_rate": field_errors["date"] / field_totals["date"] if field_totals["date"] else 0.0,
                    },
                    "total": {
                        "total": field_totals["total"],
                        "errors": field_errors["total"],
                        "error_rate": field_errors["total"] / field_totals["total"] if field_totals["total"] else 0.0,
                    },
                },
            },
            "by_category": by_category,
            "patterns": {
                **patterns,
                "ocr_confusions": self.pattern_detector.detect_ocr_confusion_patterns(error_records),
            },
            "insights": insights,
            "recommendations": recommendations,
            "errors": error_records,
        }

    def get_error_examples(
        self,
        error_type: ErrorType,
        predictions: List[Dict],
        ground_truth: List[Dict],
        ocr_results: List[str],
        limit: int = 5
    ) -> List[Dict]:
        """
        Get example errors of a specific type.
        """
        analysis = self.analyze_errors(predictions, ground_truth, ocr_results)
        examples = analysis["by_category"].get(error_type.value, {}).get("examples", [])
        return examples[:limit]

    def generate_insights(
        self,
        error_distribution: Dict,
        patterns: Optional[Dict] = None,
        total_errors: Optional[int] = None
    ) -> List[str]:
        """
        Generate actionable insights from error patterns.
        """
        insights = []

        sorted_categories = sorted(
            error_distribution.items(),
            key=lambda item: item[1].get("count", 0),
            reverse=True
        )

        for category, payload in sorted_categories[:3]:
            count = payload.get("count", 0)
            percentage = payload.get("percentage", 0.0)
            if count <= 0:
                continue

            if category == ErrorType.SUBTOTAL_CONFUSION.value:
                insights.append(
                    f"{percentage:.1f}% of errors are subtotal confusion - improve total detection heuristics"
                )
            elif category == ErrorType.DATE_PARSING_ERROR.value:
                insights.append(
                    f"{percentage:.1f}% of errors come from date parsing failures - expand parser coverage"
                )
            elif category == ErrorType.OCR_NOISE.value:
                insights.append(
                    f"{percentage:.1f}% of errors are linked to OCR noise - preprocessing and OCR cleanup may help"
                )
            elif category == ErrorType.LOW_CONFIDENCE.value:
                insights.append(
                    f"{percentage:.1f}% of errors are low-confidence predictions - consider confidence thresholding"
                )
            else:
                insights.append(
                    f"{percentage:.1f}% of errors fall into {category.replace('_', ' ')}"
                )

        if patterns:
            low_conf_rate = patterns.get("confidence_correlation", {}).get("low_conf_error_rate", 0.0)
            high_conf_rate = patterns.get("confidence_correlation", {}).get("high_conf_error_rate", 0.0)
            if low_conf_rate > high_conf_rate:
                insights.append(
                    f"Low confidence (<0.5) predictions account for {low_conf_rate * 100:.1f}% of all tracked errors"
                )

            low_quality_rate = patterns.get("ocr_quality_correlation", {}).get("low_quality_error_rate", 0.0)
            high_quality_rate = patterns.get("ocr_quality_correlation", {}).get("high_quality_error_rate", 0.0)
            if low_quality_rate > high_quality_rate:
                insights.append("OCR quality strongly correlates with errors - preprocessing may help")

            failed_formats = patterns.get("field_specific", {}).get("date", {}).get("common_formats_failed", [])
            if failed_formats:
                insights.append(
                    f"Date extraction fails most often on {failed_formats[0]}-style inputs"
                )

        if total_errors == 0:
            return ["No errors detected in the evaluated sample set"]

        return insights

    def generate_recommendations(
        self,
        error_distribution: Dict,
        patterns: Optional[Dict] = None
    ) -> List[str]:
        """Generate implementation-oriented recommendations from error analysis."""
        recommendations = []

        if ErrorType.SUBTOTAL_CONFUSION.value in error_distribution:
            recommendations.append("Add stronger penalties for 'subtotal' keyword proximity in total extraction")
        if ErrorType.DATE_PARSING_ERROR.value in error_distribution or ErrorType.DATE_FORMAT_ERROR.value in error_distribution:
            recommendations.append("Implement date format detection before date normalization")
        if ErrorType.LOW_CONFIDENCE.value in error_distribution:
            recommendations.append("Add a production confidence rejection threshold around 0.5")
        if ErrorType.OCR_NOISE.value in error_distribution:
            recommendations.append("Add OCR preprocessing or text cleanup for noisy scans")
        if patterns and patterns.get("field_specific", {}).get("total", {}).get("position_bias_issues"):
            recommendations.append("Review layout heuristics to prioritize bottom-most final total candidates")
        if not recommendations:
            recommendations.append("Review uncategorized errors and refine heuristics incrementally")

        return recommendations

    def _build_category_summary(self, error_records: List[Dict]) -> Dict:
        """Build category-level summary with examples."""
        total_errors = len(error_records)
        by_category_records = defaultdict(list)

        for error in error_records:
            by_category_records[error["error_type"]].append(error)

        summary = {}
        for category, records in by_category_records.items():
            field_counter = Counter(record["field_name"] for record in records)
            dominant_field = field_counter.most_common(1)[0][0] if field_counter else "both"
            summary[category] = {
                "count": len(records),
                "percentage": (len(records) / total_errors * 100) if total_errors else 0.0,
                "field": dominant_field if len(field_counter) == 1 else "both",
                "examples": [
                    {
                        "image_id": record["image_id"],
                        "predicted": record["predicted"],
                        "actual": record["actual"],
                        "confidence": record["confidence"],
                        "ocr_snippet": record["ocr_snippet"],
                        "explanation": record["explanation"],
                    }
                    for record in records[:5]
                ],
            }
        return dict(sorted(summary.items(), key=lambda item: item[1]["count"], reverse=True))

    def _make_ocr_snippet(self, ocr_text: str, predicted: Any, actual: Any, max_length: int = 180) -> str:
        """Create a short OCR snippet for reporting."""
        text = " ".join((ocr_text or "").split())
        if not text:
            return ""

        search_terms = [str(predicted), str(actual)]
        for term in search_terms:
            if term and term != "None":
                idx = text.lower().find(term.lower())
                if idx != -1:
                    start = max(0, idx - 60)
                    end = min(len(text), idx + 120)
                    return text[start:end]

        return text[:max_length]

    def _values_match(self, prediction: Any, actual: Any, field_name: str) -> bool:
        """Deterministic field-level comparison."""
        if prediction is None or actual is None:
            return False

        if field_name == "total":
            pred_val = normalize_total(str(prediction))
            actual_val = normalize_total(str(actual))
            if pred_val is None or actual_val is None:
                return str(prediction).strip() == str(actual).strip()
            return abs(pred_val - actual_val) < 0.01

        if field_name == "date":
            pred_date = normalize_date(str(prediction)) or str(prediction).strip()
            actual_date = normalize_date(str(actual)) or str(actual).strip()
            return pred_date == actual_date

        return str(prediction).strip() == str(actual).strip()


def generate_error_distribution_chart(error_data: Dict) -> str:
    """
    Generate ASCII bar chart of error distribution.
    """
    by_category = error_data.get("by_category", {})
    if not by_category:
        return "No categorized errors available."

    max_count = max(payload["count"] for payload in by_category.values()) or 1
    lines = ["Error Distribution:"]
    for category, payload in by_category.items():
        count = payload["count"]
        percentage = payload["percentage"]
        bar_len = int((count / max_count) * 20)
        label = category.replace("_", " ").title()
        lines.append(f"  {label:<22} {count:>4} ({percentage:>5.1f}%) {'█' * bar_len}")
    return "\n".join(lines)


def generate_confidence_vs_accuracy_plot(data: List[Dict]) -> str:
    """
    Generate scatter plot showing confidence vs accuracy.

    Returns ASCII plot.
    """
    if not data:
        return "No error data available."

    width = 20
    height = 10
    grid = [[" " for _ in range(width)] for _ in range(height)]

    for item in data:
        x = min(width - 1, max(0, int(float(item.get("confidence", 0.0)) * (width - 1))))
        accuracy = 0.0 if item.get("is_error", True) else 1.0
        y = min(height - 1, max(0, int((1.0 - accuracy) * (height - 1))))
        grid[y][x] = "●"

    lines = ["Confidence vs Accuracy (ASCII)"]
    for row in grid:
        lines.append("".join(row))
    lines.append("0.0" + " " * (width - 6) + "1.0")
    lines.append("x=confidence, y=error(1) to correct(0)")
    return "\n".join(lines)

# Made with Bob
