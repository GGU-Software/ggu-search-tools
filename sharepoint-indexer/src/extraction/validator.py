"""Validation for extracted PDF content quality."""

import re
from dataclasses import dataclass
from enum import Enum


class QualityIssue(str, Enum):
    """Types of quality issues detected in extracted text."""
    GLYPH_ENCODING = "glyph_encoding"  # PDF uses glyph names instead of text
    LOW_TEXT_RATIO = "low_text_ratio"  # Very little readable text
    GIBBERISH = "gibberish"  # High ratio of non-word characters
    EMPTY = "empty"  # No meaningful content


@dataclass
class ValidationResult:
    """Result of document validation."""
    is_valid: bool
    issues: list[QualityIssue]
    details: dict[str, any]

    @property
    def should_index(self) -> bool:
        """Whether document should be indexed (no critical issues)."""
        critical_issues = {QualityIssue.GLYPH_ENCODING, QualityIssue.EMPTY}
        return not any(issue in critical_issues for issue in self.issues)


class DocumentValidator:
    """Validate extracted document quality for indexing."""

    def __init__(
        self,
        glyph_threshold: int = 50,
        min_word_ratio: float = 0.3,
        min_words: int = 100,
    ):
        """
        Initialize validator.

        Args:
            glyph_threshold: Max glyph patterns before flagging as corrupted
            min_word_ratio: Minimum ratio of valid words to total tokens
            min_words: Minimum words for a valid document
        """
        self.glyph_threshold = glyph_threshold
        self.min_word_ratio = min_word_ratio
        self.min_words = min_words

        # Pattern for glyph-name encoding (e.g., /g50, /g51)
        self.glyph_pattern = re.compile(r'/g\d+')

        # Pattern for valid words (letters, umlauts, common punctuation)
        self.word_pattern = re.compile(r'\b[a-zA-ZäöüÄÖÜß]{2,}\b')

    def validate(self, text: str, filename: str = "") -> ValidationResult:
        """
        Validate extracted text quality.

        Args:
            text: The extracted text content
            filename: Optional filename for logging

        Returns:
            ValidationResult with validity status and any issues
        """
        issues = []
        details = {
            "filename": filename,
            "char_count": len(text),
            "word_count": len(text.split()),
        }

        # Check for empty content
        if len(text.strip()) < 50:
            issues.append(QualityIssue.EMPTY)
            details["reason"] = "Document has no meaningful content"
            return ValidationResult(is_valid=False, issues=issues, details=details)

        # Check for glyph encoding issues
        sample = text[:10000]  # Check first 10k chars
        glyph_matches = len(self.glyph_pattern.findall(sample))
        details["glyph_count"] = glyph_matches

        if glyph_matches > self.glyph_threshold:
            issues.append(QualityIssue.GLYPH_ENCODING)
            details["reason"] = f"Detected {glyph_matches} glyph patterns - PDF has encoding issues"

        # Check word ratio (valid words vs total tokens)
        tokens = text.split()
        valid_words = self.word_pattern.findall(text)

        if tokens:
            word_ratio = len(valid_words) / len(tokens)
            details["valid_word_ratio"] = round(word_ratio, 2)

            if word_ratio < self.min_word_ratio and QualityIssue.GLYPH_ENCODING not in issues:
                issues.append(QualityIssue.GIBBERISH)
                details["reason"] = f"Low valid word ratio: {word_ratio:.1%}"

        # Check minimum content
        if len(valid_words) < self.min_words:
            if QualityIssue.GLYPH_ENCODING not in issues:
                issues.append(QualityIssue.LOW_TEXT_RATIO)
                details["valid_words"] = len(valid_words)

        is_valid = len(issues) == 0
        return ValidationResult(is_valid=is_valid, issues=issues, details=details)

    def validate_markdown(self, markdown: str, filename: str = "") -> ValidationResult:
        """
        Validate markdown content (convenience wrapper).

        Strips markdown formatting before validation.
        """
        # Remove markdown formatting for cleaner validation
        text = markdown
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)  # Headers
        text = re.sub(r'\|[-:]+\|', '', text)  # Table separators
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)  # Comments
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)  # Images

        return self.validate(text, filename)
