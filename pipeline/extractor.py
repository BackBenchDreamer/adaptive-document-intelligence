"""
Field Extraction Module

Extracts structured fields (date, total, invoice_number) from OCR text
using heuristic-based scoring methods.

Author: Adaptive Document Intelligence System
Phase: 4 - Field Extraction Engine
"""

import re
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class FieldExtractor(ABC):
    """
    Abstract base class for field extractors.
    
    Each field type (date, total, invoice_number) has its own extractor
    that implements specific extraction logic and scoring.
    """
    
    @abstractmethod
    def extract(self, text: str) -> Dict:
        """
        Extract field from text.
        
        Args:
            text: OCR text to extract from
            
        Returns:
            {
                'value': Any,           # Extracted value (or None)
                'confidence': float,    # Extraction confidence [0,1]
                'candidates': List,     # All candidates considered
                'method': str,          # Extraction method used
                'metadata': dict        # Additional info
            }
        """
        pass


class DateExtractor(FieldExtractor):
    """
    Extract date from OCR text.
    
    Strategy:
    1. Find all date-like patterns in text
    2. Score each candidate based on:
       - Pattern match strength
       - Proximity to keywords ("date", "invoice date")
       - Position in document (dates usually near top)
       - Format validity
    3. Return highest scoring candidate
    
    Supported formats:
    - DD/MM/YYYY, MM/DD/YYYY
    - DD-MM-YYYY, MM-DD-YYYY
    - YYYY-MM-DD
    - DD Mon YYYY, Mon DD YYYY
    - Compact: DDMMYYYY, YYYYMMDD
    """
    
    def __init__(self):
        """Initialize date patterns and keywords."""
        # Date patterns (pattern, format_name, score_weight)
        self.patterns = [
            # Standard formats with separators
            (r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b', 'DD/MM/YYYY', 1.0),
            (r'\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b', 'YYYY-MM-DD', 1.0),
            
            # Month name formats
            (r'\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})\b', 
             'DD Mon YYYY', 0.95),
            (r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),?\s+(\d{4})\b',
             'Mon DD YYYY', 0.95),
            
            # Compact formats (less reliable)
            (r'\b(\d{8})\b', 'DDMMYYYY/YYYYMMDD', 0.7),
        ]
        
        # Keywords that indicate date fields
        self.positive_keywords = [
            'date', 'invoice date', 'receipt date', 'issued', 'dated',
            'on', 'as of', 'bill date', 'transaction date'
        ]
        
        # Month name mapping
        self.month_map = {
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
    
    def extract(self, text: str) -> Dict:
        """Extract date from text."""
        start_time = time.time()
        
        if not text or not text.strip():
            return {
                'value': None,
                'confidence': 0.0,
                'candidates': [],
                'method': 'no_text',
                'metadata': {'extraction_time': time.time() - start_time}
            }
        
        # Find all date candidates
        candidates = self._find_date_candidates(text)
        
        if not candidates:
            logger.debug("No date candidates found in text")
            return {
                'value': None,
                'confidence': 0.0,
                'candidates': [],
                'method': 'no_candidates',
                'metadata': {'extraction_time': time.time() - start_time}
            }
        
        # Score each candidate
        scored_candidates = []
        for date_str, position, format_pattern, format_weight in candidates:
            score = self._score_date_candidate(date_str, position, text, format_weight)
            
            # Try to parse and normalize the date
            normalized_date = self._normalize_date(date_str, format_pattern)
            
            if normalized_date:
                scored_candidates.append({
                    'raw_value': date_str,
                    'value': normalized_date,
                    'score': score,
                    'position': position,
                    'format': format_pattern
                })
        
        if not scored_candidates:
            logger.debug("No valid date candidates after parsing")
            return {
                'value': None,
                'confidence': 0.0,
                'candidates': [c[0] for c in candidates],
                'method': 'invalid_dates',
                'metadata': {'extraction_time': time.time() - start_time}
            }
        
        # Sort by score and select best
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        best = scored_candidates[0]
        
        logger.info(f"Extracted date: {best['value']} (confidence: {best['score']:.2f})")
        
        return {
            'value': best['value'],
            'confidence': best['score'],
            'raw_value': best['raw_value'],
            'candidates': scored_candidates,
            'method': 'keyword_proximity' if best['score'] > 0.7 else 'pattern_match',
            'metadata': {
                'extraction_time': time.time() - start_time,
                'format': best['format'],
                'position': best['position']
            }
        }
    
    def _find_date_candidates(self, text: str) -> List[Tuple[str, int, str, float]]:
        """
        Find all date candidates in text.
        
        Returns:
            List of (date_string, position, format_pattern, format_weight)
        """
        candidates = []
        text_lower = text.lower()
        
        for pattern, format_name, format_weight in self.patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                date_str = match.group(0)
                position = match.start()
                candidates.append((date_str, position, format_name, format_weight))
        
        return candidates
    
    def _score_date_candidate(
        self, 
        candidate: str, 
        position: int, 
        text: str,
        format_weight: float
    ) -> float:
        """
        Score a date candidate.
        
        Scoring factors:
        - Keyword proximity: +0.3 if near "date", "invoice date"
        - Position bias: +0.2 if in top 30% of text
        - Format validity: +0.3 based on format weight
        - Context: +0.2 if surrounded by relevant text
        
        Returns:
            Score in [0, 1]
        """
        score = 0.0
        text_lower = text.lower()
        text_length = len(text)
        
        # 1. Keyword proximity (40% weight)
        keyword_score = 0.0
        context_window = 50  # characters before and after
        context_start = max(0, position - context_window)
        context_end = min(text_length, position + len(candidate) + context_window)
        context = text_lower[context_start:context_end]
        
        for keyword in self.positive_keywords:
            if keyword in context:
                keyword_score = 1.0
                break
        
        score += keyword_score * 0.4
        
        # 2. Position bias (30% weight) - prefer top 30%
        relative_pos = position / text_length if text_length > 0 else 0
        position_score = 1.0 if relative_pos < 0.3 else 0.5
        score += position_score * 0.3
        
        # 3. Format validity (20% weight)
        score += format_weight * 0.2
        
        # 4. Context score (10% weight) - check for colon or label
        context_score = 0.0
        if position > 0:
            before_text = text[max(0, position - 10):position]
            if ':' in before_text or 'date' in before_text.lower():
                context_score = 1.0
        
        score += context_score * 0.1
        
        return min(1.0, score)
    
    def _normalize_date(self, date_str: str, format_pattern: str) -> Optional[str]:
        """
        Normalize date to ISO format (YYYY-MM-DD).
        
        Args:
            date_str: Raw date string
            format_pattern: Format pattern name
            
        Returns:
            ISO formatted date string or None if invalid
        """
        try:
            # Handle different format patterns
            if format_pattern in ['DD/MM/YYYY', 'DD-MM-YYYY']:
                # Parse DD/MM/YYYY or DD-MM-YYYY
                parts = re.split(r'[/-]', date_str)
                if len(parts) == 3:
                    day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
                    date_obj = datetime(year, month, day)
                    return date_obj.strftime('%Y-%m-%d')
            
            elif format_pattern == 'YYYY-MM-DD':
                # Already in ISO format, just validate
                parts = re.split(r'[/-]', date_str)
                if len(parts) == 3:
                    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
                    date_obj = datetime(year, month, day)
                    return date_obj.strftime('%Y-%m-%d')
            
            elif format_pattern == 'DD Mon YYYY':
                # Parse DD Mon YYYY
                match = re.match(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', date_str)
                if match:
                    day = int(match.group(1))
                    month_str = match.group(2)[:3].lower()
                    year = int(match.group(3))
                    month = self.month_map.get(month_str)
                    if month:
                        date_obj = datetime(year, month, day)
                        return date_obj.strftime('%Y-%m-%d')
            
            elif format_pattern == 'Mon DD YYYY':
                # Parse Mon DD YYYY
                match = re.match(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})', date_str)
                if match:
                    month_str = match.group(1)[:3].lower()
                    day = int(match.group(2))
                    year = int(match.group(3))
                    month = self.month_map.get(month_str)
                    if month:
                        date_obj = datetime(year, month, day)
                        return date_obj.strftime('%Y-%m-%d')
            
            elif format_pattern == 'DDMMYYYY/YYYYMMDD':
                # Try both DDMMYYYY and YYYYMMDD
                if len(date_str) == 8:
                    # Try YYYYMMDD first (more reliable)
                    try:
                        year = int(date_str[:4])
                        month = int(date_str[4:6])
                        day = int(date_str[6:8])
                        if 1900 <= year <= 2100:
                            date_obj = datetime(year, month, day)
                            return date_obj.strftime('%Y-%m-%d')
                    except:
                        pass
                    
                    # Try DDMMYYYY
                    try:
                        day = int(date_str[:2])
                        month = int(date_str[2:4])
                        year = int(date_str[4:8])
                        date_obj = datetime(year, month, day)
                        return date_obj.strftime('%Y-%m-%d')
                    except:
                        pass
        
        except (ValueError, IndexError) as e:
            logger.debug(f"Failed to parse date '{date_str}': {e}")
            return None
        
        return None


class TotalExtractor(FieldExtractor):
    """
    Extract total amount from OCR text.
    
    Strategy:
    1. Extract ALL numeric candidates (with currency symbols)
    2. Normalize values to float
    3. Apply scoring:
       - Keyword proximity ("total", "amount due", "balance")
       - Positional bias (bottom-heavy preference)
       - Numeric format validity
       - Penalize: "subtotal", "tax", "discount", "change"
    4. Select highest scoring candidate
    
    This is the MOST CRITICAL extractor - must handle:
    - Multiple amounts on receipt
    - Subtotal vs total confusion
    - Tax amounts
    - Currency symbols
    - Thousands separators
    """
    
    def __init__(self):
        """Initialize patterns and keywords."""
        # Amount patterns
        self.patterns = [
            # With currency symbols
            r'[$€£¥₹]\s*(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)',
            r'(\d{1,3}(?:[,\s]\d{3})*(?:\.\d{2})?)\s*[$€£¥₹]',
            
            # Without currency symbols (more general)
            r'\b(\d{1,3}(?:[,\s]\d{3})*\.\d{2})\b',
            r'\b(\d+\.\d{2})\b',
        ]
        
        # Positive keywords (indicate total amount)
        self.positive_keywords = [
            'total', 'amount due', 'balance', 'grand total', 'net total',
            'amount', 'pay', 'payment', 'due', 'payable'
        ]
        
        # Negative keywords (indicate NOT total)
        self.negative_keywords = [
            'subtotal', 'sub total', 'sub-total', 'tax', 'gst', 'vat',
            'discount', 'change', 'tendered', 'cash', 'card', 'paid'
        ]
    
    def extract(self, text: str) -> Dict:
        """Extract total amount from text."""
        start_time = time.time()
        
        if not text or not text.strip():
            return {
                'value': None,
                'confidence': 0.0,
                'candidates': [],
                'method': 'no_text',
                'metadata': {'extraction_time': time.time() - start_time}
            }
        
        # Find all amount candidates
        candidates = self._find_amount_candidates(text)
        
        if not candidates:
            logger.debug("No amount candidates found in text")
            return {
                'value': None,
                'confidence': 0.0,
                'candidates': [],
                'method': 'no_candidates',
                'metadata': {'extraction_time': time.time() - start_time}
            }
        
        # Score each candidate
        scored_candidates = []
        max_amount = max(c[0] for c in candidates)
        
        for amount, position, original in candidates:
            score = self._score_amount_candidate(
                amount, position, original, text, max_amount
            )
            
            scored_candidates.append({
                'value': amount,
                'raw_value': original,
                'score': score,
                'position': position
            })
        
        # Sort by score and select best
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        best = scored_candidates[0]
        
        logger.info(f"Extracted total: ${best['value']:.2f} (confidence: {best['score']:.2f})")
        
        return {
            'value': best['value'],
            'confidence': best['score'],
            'raw_value': best['raw_value'],
            'candidates': scored_candidates,
            'method': 'bottom_position_keyword' if best['score'] > 0.7 else 'highest_amount',
            'metadata': {
                'extraction_time': time.time() - start_time,
                'position': best['position'],
                'num_candidates': len(candidates)
            }
        }
    
    def _find_amount_candidates(self, text: str) -> List[Tuple[float, int, str]]:
        """
        Find all amount candidates in text.
        
        Returns:
            List of (amount_value, position, original_string)
        """
        candidates = []
        seen_positions = set()
        
        for pattern in self.patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                position = match.start()
                
                # Avoid duplicate candidates at same position
                if position in seen_positions:
                    continue
                
                original = match.group(0)
                
                # Extract numeric part
                numeric_str = re.sub(r'[^\d.]', '', match.group(1) if match.lastindex else match.group(0))
                
                try:
                    amount = float(numeric_str)
                    
                    # Sanity check: reasonable amount range
                    if 0.01 <= amount <= 100000:
                        candidates.append((amount, position, original))
                        seen_positions.add(position)
                except ValueError:
                    continue
        
        return candidates
    
    def _score_amount_candidate(
        self,
        amount: float,
        position: int,
        original: str,
        text: str,
        max_amount: float
    ) -> float:
        """
        Score an amount candidate.
        
        Scoring factors:
        - Keyword proximity: +0.4 if near "total", "amount due"
        - Position bias: +0.3 if in bottom 40% of text
        - Format validity: +0.2 if proper currency format
        - Penalty: -0.5 if near "subtotal", "tax", "discount"
        - Magnitude: +0.1 if largest amount (likely total)
        
        Returns:
            Score in [0, 1]
        """
        score = 0.0
        text_lower = text.lower()
        text_length = len(text)
        
        # 1. Keyword proximity (40% weight)
        keyword_score = 0.0
        context_window = 30  # characters before and after
        context_start = max(0, position - context_window)
        context_end = min(text_length, position + len(original) + context_window)
        context = text_lower[context_start:context_end]
        
        # Check positive keywords
        for keyword in self.positive_keywords:
            if keyword in context:
                keyword_score = 1.0
                break
        
        score += keyword_score * 0.4
        
        # 2. Position bias (30% weight) - prefer bottom 40%
        relative_pos = position / text_length if text_length > 0 else 0
        position_score = 1.0 if relative_pos > 0.6 else 0.5
        score += position_score * 0.3
        
        # 3. Format validity (20% weight)
        format_score = 0.0
        if '$' in original or '€' in original or '£' in original:
            format_score = 1.0
        elif re.match(r'\d+\.\d{2}$', original.strip()):
            format_score = 0.8
        
        score += format_score * 0.2
        
        # 4. Magnitude bonus (10% weight) - largest amount likely total
        if amount == max_amount:
            score += 0.1
        
        # 5. Penalties - check negative keywords
        penalty = 0.0
        for neg_keyword in self.negative_keywords:
            if neg_keyword in context:
                penalty = 0.5
                break
        
        score = max(0.0, score - penalty)
        
        return min(1.0, score)


class InvoiceNumberExtractor(FieldExtractor):
    """
    Extract invoice/receipt number from OCR text.
    
    Strategy:
    1. Find alphanumeric patterns
    2. Score based on:
       - Proximity to keywords ("invoice", "receipt", "no", "#")
       - Position (usually near top)
       - Format (length, character mix)
    3. Return highest scoring candidate
    
    Patterns:
    - INV-12345
    - #123456
    - Receipt: 789012
    - Pure numeric: 123456789
    """
    
    def __init__(self):
        """Initialize patterns and keywords."""
        # Invoice number patterns
        self.patterns = [
            # With prefix
            r'\b(INV[:-]?\s*\d+)\b',
            r'\b(REC[:-]?\s*\d+)\b',
            r'\b(#\s*\d+)\b',
            
            # After keywords
            r'(?:invoice|receipt|no|number|ref|reference)[:\s]+([A-Z0-9-]+)',
            
            # Standalone alphanumeric (6-15 chars)
            r'\b([A-Z0-9]{6,15})\b',
        ]
        
        # Keywords that indicate invoice number
        self.positive_keywords = [
            'invoice', 'receipt', 'no', 'number', '#', 'ref', 'reference',
            'bill', 'transaction', 'order'
        ]
    
    def extract(self, text: str) -> Dict:
        """Extract invoice number from text."""
        start_time = time.time()
        
        if not text or not text.strip():
            return {
                'value': None,
                'confidence': 0.0,
                'candidates': [],
                'method': 'no_text',
                'metadata': {'extraction_time': time.time() - start_time}
            }
        
        # Find all invoice number candidates
        candidates = self._find_invoice_candidates(text)
        
        if not candidates:
            logger.debug("No invoice number candidates found in text")
            return {
                'value': None,
                'confidence': 0.0,
                'candidates': [],
                'method': 'no_candidates',
                'metadata': {'extraction_time': time.time() - start_time}
            }
        
        # Score each candidate
        scored_candidates = []
        for inv_num, position in candidates:
            score = self._score_invoice_candidate(inv_num, position, text)
            
            scored_candidates.append({
                'value': inv_num,
                'raw_value': inv_num,
                'score': score,
                'position': position
            })
        
        # Sort by score and select best
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        best = scored_candidates[0]
        
        logger.info(f"Extracted invoice number: {best['value']} (confidence: {best['score']:.2f})")
        
        return {
            'value': best['value'],
            'confidence': best['score'],
            'raw_value': best['raw_value'],
            'candidates': scored_candidates,
            'method': 'keyword_proximity' if best['score'] > 0.7 else 'pattern_match',
            'metadata': {
                'extraction_time': time.time() - start_time,
                'position': best['position']
            }
        }
    
    def _find_invoice_candidates(self, text: str) -> List[Tuple[str, int]]:
        """
        Find all invoice number candidates in text.
        
        Returns:
            List of (invoice_number, position)
        """
        candidates = []
        seen_values = set()
        
        for pattern in self.patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                inv_num = match.group(1) if match.lastindex else match.group(0)
                inv_num = inv_num.strip()
                position = match.start()
                
                # Avoid duplicates
                if inv_num.lower() not in seen_values:
                    candidates.append((inv_num, position))
                    seen_values.add(inv_num.lower())
        
        return candidates
    
    def _score_invoice_candidate(
        self,
        candidate: str,
        position: int,
        text: str
    ) -> float:
        """
        Score an invoice number candidate.
        
        Scoring factors:
        - Keyword proximity: +0.5 if near relevant keywords
        - Position bias: +0.3 if in top 30% of text
        - Format validity: +0.2 based on length and character mix
        
        Returns:
            Score in [0, 1]
        """
        score = 0.0
        text_lower = text.lower()
        text_length = len(text)
        
        # 1. Keyword proximity (50% weight)
        keyword_score = 0.0
        context_window = 40
        context_start = max(0, position - context_window)
        context_end = min(text_length, position + len(candidate) + context_window)
        context = text_lower[context_start:context_end]
        
        for keyword in self.positive_keywords:
            if keyword in context:
                keyword_score = 1.0
                break
        
        score += keyword_score * 0.5
        
        # 2. Position bias (30% weight) - prefer top 30%
        relative_pos = position / text_length if text_length > 0 else 0
        position_score = 1.0 if relative_pos < 0.3 else 0.5
        score += position_score * 0.3
        
        # 3. Format validity (20% weight)
        format_score = 0.0
        length = len(candidate)
        
        # Prefer 6-12 character length
        if 6 <= length <= 12:
            format_score = 1.0
        elif 4 <= length <= 15:
            format_score = 0.7
        else:
            format_score = 0.3
        
        # Bonus for alphanumeric mix
        has_letters = any(c.isalpha() for c in candidate)
        has_digits = any(c.isdigit() for c in candidate)
        if has_letters and has_digits:
            format_score = min(1.0, format_score + 0.2)
        
        score += format_score * 0.2
        
        return min(1.0, score)


class ExtractionManager:
    """
    Manages all field extractors.
    
    Coordinates extraction of all fields from OCR text.
    """
    
    def __init__(self):
        """Initialize all extractors."""
        self.date_extractor = DateExtractor()
        self.total_extractor = TotalExtractor()
        self.invoice_extractor = InvoiceNumberExtractor()
        
        logger.info("ExtractionManager initialized with all extractors")
    
    def extract_fields(self, ocr_result: Dict) -> Dict:
        """
        Extract all fields from OCR result.
        
        Args:
            ocr_result: Output from OCR module with structure:
                {
                    'text': str,
                    'confidence': float,
                    'metadata': dict
                }
            
        Returns:
            {
                'date': {
                    'value': str,           # ISO format or None
                    'confidence': float,
                    'raw_value': str,
                    'method': str
                },
                'total': {
                    'value': float,         # Amount or None
                    'confidence': float,
                    'raw_value': str,
                    'method': str
                },
                'invoice_number': {
                    'value': str,           # Invoice number or None
                    'confidence': float,
                    'raw_value': str,
                    'method': str
                },
                'metadata': {
                    'ocr_confidence': float,
                    'extraction_time': float,
                    'text_length': int,
                    'candidates_considered': dict
                }
            }
        """
        start_time = time.time()
        
        # Extract text from OCR result
        text = ocr_result.get('text', '')
        ocr_confidence = ocr_result.get('confidence', 0.0)
        
        logger.info(f"Starting field extraction from {len(text)} characters of text")
        
        # Extract each field
        date_result = self.date_extractor.extract(text)
        total_result = self.total_extractor.extract(text)
        invoice_result = self.invoice_extractor.extract(text)
        
        # Build result
        result = {
            'date': {
                'value': date_result['value'],
                'confidence': date_result['confidence'],
                'raw_value': date_result.get('raw_value', ''),
                'method': date_result['method']
            },
            'total': {
                'value': total_result['value'],
                'confidence': total_result['confidence'],
                'raw_value': total_result.get('raw_value', ''),
                'method': total_result['method']
            },
            'invoice_number': {
                'value': invoice_result['value'],
                'confidence': invoice_result['confidence'],
                'raw_value': invoice_result.get('raw_value', ''),
                'method': invoice_result['method']
            },
            'metadata': {
                'ocr_confidence': ocr_confidence,
                'extraction_time': time.time() - start_time,
                'text_length': len(text),
                'candidates_considered': {
                    'date': len(date_result.get('candidates', [])),
                    'total': len(total_result.get('candidates', [])),
                    'invoice_number': len(invoice_result.get('candidates', []))
                }
            }
        }
        
        logger.info(
            f"Field extraction complete in {result['metadata']['extraction_time']:.3f}s: "
            f"date={date_result['value']}, total={total_result['value']}, "
            f"invoice={invoice_result['value']}"
        )
        
        return result

# Made with Bob
