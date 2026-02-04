#!/usr/bin/env python3
"""
Test PDF extraction with Docling on the 3 test documents.
Analyzes text quality, structure detection, and German character handling.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extraction import PDFExtractor, DocumentValidator


def analyze_document(extractor: PDFExtractor, validator: DocumentValidator, pdf_path: Path) -> dict:
    """Extract and analyze a single PDF document."""

    print(f"\n{'=' * 70}")
    print(f"Document: {pdf_path.name}")
    print("=" * 70)

    # Extract markdown (primary output)
    print("\nExtracting with Docling (this may take a moment)...")
    markdown = extractor.extract_markdown(pdf_path)

    # Basic metrics
    char_count = len(markdown)
    word_count = len(markdown.split())
    line_count = len(markdown.split('\n'))

    print("\n--- Metrics ---")
    print(f"  Characters:  {char_count:,}")
    print(f"  Words:       {word_count:,}")
    print(f"  Lines:       {line_count:,}")

    # German character check
    print("\n--- German Character Check ---")
    german_chars = {'ä', 'ö', 'ü', 'Ä', 'Ö', 'Ü', 'ß'}
    found_chars = set()
    for char in german_chars:
        if char in markdown:
            found_chars.add(char)

    if found_chars:
        print(f"  Found: {', '.join(sorted(found_chars))}")
    else:
        print("  No German special characters found")

    # Structure detection (headings)
    print("\n--- Structure Detection (Headings) ---")
    headings = []
    for line in markdown.split('\n'):
        line = line.strip()
        if line.startswith('#'):
            # Count heading level
            level = len(line) - len(line.lstrip('#'))
            text = line.lstrip('#').strip()
            if text and level <= 4:
                headings.append((level, text[:60]))

    if headings:
        print(f"  Found {len(headings)} headings:")
        for level, text in headings[:15]:
            indent = "  " * level
            print(f"    {'#' * level} {text}")
        if len(headings) > 15:
            print(f"    ... and {len(headings) - 15} more")
    else:
        print("  No markdown headings detected")

    # Table detection
    print("\n--- Table Detection ---")
    table_count = markdown.count('|---')
    if table_count > 0:
        print(f"  Found {table_count} table(s)")
    else:
        print("  No tables detected")

    # Text sample
    print("\n--- Text Sample (first 600 chars) ---")
    sample = markdown[:600]
    if len(markdown) > 600:
        sample += "\n..."
    for line in sample.split('\n')[:20]:
        print(f"  {line}")

    # Validate content quality
    print("\n--- Quality Validation ---")
    validation = validator.validate_markdown(markdown, pdf_path.name)

    if validation.is_valid:
        print("  ✅ VALID - Document passes quality checks")
    else:
        print("  ❌ INVALID - Quality issues detected:")
        for issue in validation.issues:
            print(f"     - {issue.value}: {validation.details.get('reason', '')}")

    print(f"  Should index: {validation.should_index}")
    if 'glyph_count' in validation.details:
        print(f"  Glyph patterns: {validation.details['glyph_count']}")
    if 'valid_word_ratio' in validation.details:
        print(f"  Valid word ratio: {validation.details['valid_word_ratio']:.0%}")

    # Save markdown to file for inspection
    output_path = pdf_path.parent / f"{pdf_path.stem}.md"
    output_path.write_text(markdown, encoding='utf-8')
    print(f"\n  Saved full markdown to: {output_path.name}")

    return {
        "filename": pdf_path.name,
        "chars": char_count,
        "words": word_count,
        "headings": len(headings),
        "tables": table_count,
        "german_chars": bool(found_chars),
        "valid": validation.is_valid,
        "should_index": validation.should_index,
        "issues": [i.value for i in validation.issues],
    }


def main():
    """Run extraction test on all test documents."""

    downloads_dir = Path(__file__).parent.parent / "downloads"

    if not downloads_dir.exists():
        print(f"ERROR: Downloads directory not found: {downloads_dir}")
        print("Run fetch_test_documents.py first.")
        return

    pdf_files = list(downloads_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"ERROR: No PDF files found in {downloads_dir}")
        return

    print(f"Found {len(pdf_files)} PDF files to analyze")
    print("Using Docling with OCR enabled")

    # Initialize extractor and validator
    extractor = PDFExtractor(enable_ocr=True)
    validator = DocumentValidator()
    results = []

    for pdf_path in sorted(pdf_files):
        try:
            result = analyze_document(extractor, validator, pdf_path)
            results.append(result)
        except Exception as e:
            print(f"\nERROR processing {pdf_path.name}: {e}")
            results.append({
                "filename": pdf_path.name,
                "chars": 0,
                "words": 0,
                "headings": 0,
                "tables": 0,
                "german_chars": False,
                "error": str(e),
            })

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print("\n| Document | Words | Headings | Tables | German | Index? |")
    print("|----------|-------|----------|--------|--------|--------|")
    for r in results:
        name = r["filename"][:30] + "..." if len(r["filename"]) > 33 else r["filename"]
        german = "Yes" if r["german_chars"] else "No"
        index = "✅" if r.get("should_index", False) else "❌"
        error = " (ERROR)" if r.get("error") else ""
        print(f"| {name:33} | {r['words']:5} | {r['headings']:8} | {r['tables']:6} | {german:6} | {index:6} |{error}")

    # Show issues for invalid documents
    invalid = [r for r in results if not r.get("should_index", True)]
    if invalid:
        print("\n--- Documents with Quality Issues ---")
        for r in invalid:
            print(f"  {r['filename']}: {', '.join(r.get('issues', []))}")

    valid_count = sum(1 for r in results if r.get("should_index", False))
    print(f"\nTotal: {valid_count}/{len(results)} documents valid for indexing")
    print("Markdown files saved to downloads/ folder for inspection.")


if __name__ == "__main__":
    main()
