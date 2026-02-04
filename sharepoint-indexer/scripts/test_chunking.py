#!/usr/bin/env python3
"""
Test the section-aware chunking on extracted markdown files.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chunking import SectionChunker, Chunk


def analyze_chunks(chunks: list[Chunk]) -> dict:
    """Analyze chunk statistics."""
    if not chunks:
        return {"count": 0}

    sizes = [c.char_count for c in chunks]
    words = [c.word_count for c in chunks]

    return {
        "count": len(chunks),
        "total_chars": sum(sizes),
        "total_words": sum(words),
        "avg_chars": sum(sizes) // len(sizes),
        "min_chars": min(sizes),
        "max_chars": max(sizes),
        "with_tables": sum(1 for c in chunks if c.metadata.has_table),
        "with_lists": sum(1 for c in chunks if c.metadata.has_list),
        "unique_sections": len(set(c.metadata.section_title for c in chunks if c.metadata.section_title)),
    }


def test_document(chunker: SectionChunker, md_path: Path) -> dict:
    """Test chunking on a single document."""
    print(f"\n{'=' * 70}")
    print(f"Document: {md_path.name}")
    print("=" * 70)

    # Read markdown
    markdown = md_path.read_text(encoding='utf-8')

    # Chunk it
    doc_id = md_path.stem[:20]  # Simple ID from filename
    chunks = chunker.chunk_document(
        markdown=markdown,
        document_id=doc_id,
        filename=md_path.name,
        source_url=f"https://sharepoint.example.com/{md_path.name}",
    )

    # Analyze
    stats = analyze_chunks(chunks)

    print(f"\n--- Statistics ---")
    print(f"  Total chunks:     {stats['count']}")
    print(f"  Total words:      {stats['total_words']:,}")
    print(f"  Avg chunk size:   {stats['avg_chars']:,} chars")
    print(f"  Min chunk size:   {stats['min_chars']:,} chars")
    print(f"  Max chunk size:   {stats['max_chars']:,} chars")
    print(f"  Chunks w/ tables: {stats['with_tables']}")
    print(f"  Chunks w/ lists:  {stats['with_lists']}")
    print(f"  Unique sections:  {stats['unique_sections']}")

    # Show first few chunks
    print(f"\n--- Sample Chunks ---")
    for i, chunk in enumerate(chunks[:5]):
        meta = chunk.metadata
        section = meta.section_title or "(no section)"
        preview = chunk.content[:100].replace('\n', ' ')
        if len(chunk.content) > 100:
            preview += "..."

        print(f"\n  Chunk {i + 1}/{len(chunks)}: {section}")
        print(f"    ID:    {chunk.id[:40]}...")
        print(f"    Path:  {meta.section_path or 'N/A'}")
        print(f"    Size:  {chunk.char_count} chars, {chunk.word_count} words")
        print(f"    Table: {meta.has_table}, List: {meta.has_list}")
        print(f"    Preview: {preview}")

    if len(chunks) > 5:
        print(f"\n  ... and {len(chunks) - 5} more chunks")

    return stats


def main():
    """Test chunking on all extracted markdown files."""
    downloads_dir = Path(__file__).parent.parent / "downloads"

    md_files = list(downloads_dir.glob("*.md"))
    if not md_files:
        print(f"ERROR: No markdown files found in {downloads_dir}")
        print("Run test_extraction.py first to generate markdown files.")
        return

    print(f"Found {len(md_files)} markdown files")

    # Initialize chunker with default settings
    chunker = SectionChunker(
        max_chunk_size=1500,  # ~300-400 tokens
        min_chunk_size=200,
        overlap_size=100,
    )

    results = []
    for md_path in sorted(md_files):
        try:
            stats = test_document(chunker, md_path)
            stats["filename"] = md_path.name
            results.append(stats)
        except Exception as e:
            print(f"\nERROR processing {md_path.name}: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    print("\n| Document | Chunks | Words | Avg Size | Tables | Lists |")
    print("|----------|--------|-------|----------|--------|-------|")
    for r in results:
        name = r["filename"][:30] + "..." if len(r["filename"]) > 33 else r["filename"]
        print(f"| {name:33} | {r['count']:6} | {r['total_words']:5} | {r['avg_chars']:8} | {r['with_tables']:6} | {r['with_lists']:5} |")

    total_chunks = sum(r["count"] for r in results)
    total_words = sum(r["total_words"] for r in results)
    print(f"\nTotal: {total_chunks} chunks, {total_words:,} words across {len(results)} documents")


if __name__ == "__main__":
    main()
