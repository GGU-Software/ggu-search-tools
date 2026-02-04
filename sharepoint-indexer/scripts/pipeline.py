#!/usr/bin/env python3
"""
RAG Pipeline for SharePoint PDFs.

Workflow:
1. Fetch PDFs from SharePoint (or use local downloads/)
2. Extract text with Docling
3. Validate quality (skip corrupted PDFs)
4. Prepare for Pinecone upload

Usage:
    python scripts/pipeline.py --extract    # Extract PDFs to markdown
    python scripts/pipeline.py --validate   # Validate extracted markdown
    python scripts/pipeline.py --prepare    # Prepare upload batch (dry run)
    python scripts/pipeline.py --upload     # Actually upload to Pinecone (requires confirmation)
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

# Lazy imports to avoid loading heavy dependencies unnecessarily
# from src.config import get_settings
# from src.extraction import PDFExtractor, DocumentValidator, QualityIssue
# from src.pinecone import PineconeAssistant


def extract_pdfs(downloads_dir: Path, output_dir: Path) -> list[dict]:
    """Extract all PDFs to markdown files."""
    from src.extraction import PDFExtractor

    pdf_files = list(downloads_dir.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in {downloads_dir}")
        return []

    print(f"Found {len(pdf_files)} PDF files")
    print("Extracting with Docling (this may take a while)...\n")

    extractor = PDFExtractor(enable_ocr=True)
    results = []

    for i, pdf_path in enumerate(sorted(pdf_files), 1):
        print(f"[{i}/{len(pdf_files)}] {pdf_path.name}...", end=" ", flush=True)

        try:
            markdown = extractor.extract_markdown(pdf_path)
            output_path = output_dir / f"{pdf_path.stem}.md"
            output_path.write_text(markdown, encoding='utf-8')

            word_count = len(markdown.split())
            print(f"OK ({word_count:,} words)")

            results.append({
                "pdf": pdf_path.name,
                "markdown": output_path.name,
                "words": word_count,
                "success": True,
            })
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "pdf": pdf_path.name,
                "success": False,
                "error": str(e),
            })

    # Summary
    successful = sum(1 for r in results if r["success"])
    print(f"\nExtracted: {successful}/{len(results)} PDFs")

    return results


def validate_markdown(output_dir: Path) -> list[dict]:
    """Validate all extracted markdown files."""
    from src.extraction.validator import DocumentValidator

    md_files = list(output_dir.glob("*.md"))

    if not md_files:
        print(f"No markdown files found in {output_dir}")
        return []

    print(f"Validating {len(md_files)} markdown files...\n")

    validator = DocumentValidator()
    results = []

    for md_path in sorted(md_files):
        content = md_path.read_text(encoding='utf-8')
        validation = validator.validate_markdown(content, md_path.name)

        status = "[OK] VALID" if validation.should_index else "[!!] SKIP"
        issues = ", ".join(i.value for i in validation.issues) if validation.issues else "none"

        print(f"  {status} {md_path.name}")
        if not validation.should_index:
            print(f"         Issues: {issues}")

        results.append({
            "filename": md_path.name,
            "path": str(md_path),
            "should_index": validation.should_index,
            "issues": [i.value for i in validation.issues],
            "word_count": validation.details.get("word_count", 0),
        })

    # Summary
    valid = sum(1 for r in results if r["should_index"])
    print(f"\nValid for indexing: {valid}/{len(results)} documents")

    return results


def prepare_upload(output_dir: Path, config_path: Path = None) -> list[dict]:
    """Prepare documents for upload (dry run)."""
    import yaml
    from src.config import get_settings
    from src.indexing import IndexingFilter

    # First validate
    validation_results = validate_markdown(output_dir)

    # Filter to valid documents
    valid_docs = [r for r in validation_results if r["should_index"]]

    if not valid_docs:
        print("\nNo valid documents to upload.")
        return []

    # Apply indexing filter
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "indexing.yaml"

    idx_filter = IndexingFilter(config_path=config_path)
    filter_status = idx_filter.get_status()

    print(f"\n{'=' * 60}")
    print("INDEXING FILTER")
    print('=' * 60)
    print(f"  Mode: {filter_status['mode']}")
    if filter_status['mode'] == 'whitelist':
        print(f"  Whitelist entries: {filter_status['whitelist_count']}")
    else:
        print(f"  Include patterns: {filter_status['include_patterns']}")
        print(f"  Exclude patterns: {filter_status['exclude_patterns']}")

    included, excluded = idx_filter.filter_documents(valid_docs)

    if excluded:
        print(f"\n  Filtered out ({len(excluded)} docs):")
        for doc in excluded:
            print(f"    - {doc['filename']}")

    if not included:
        print("\nNo documents match the indexing filter.")
        print("Edit config/indexing.yaml to add documents to the whitelist.")
        return []

    # Load registry to get web_url for each document
    registry_path = Path(__file__).parent.parent / "config" / "norms-registry.yaml"
    url_lookup = {}
    if registry_path.exists():
        with open(registry_path, 'r', encoding='utf-8') as f:
            registry = yaml.safe_load(f)
        for norm in registry.get('norms', []):
            # Map PDF filename to web_url
            pdf_file = norm.get('sharepoint_file')
            web_url = norm.get('web_url')
            if pdf_file and web_url:
                # Also map the markdown filename
                md_file = pdf_file[:-4] + '.md' if pdf_file.lower().endswith('.pdf') else pdf_file
                url_lookup[md_file] = web_url
                url_lookup[pdf_file] = web_url

    print(f"\n{'=' * 60}")
    print("UPLOAD PREPARATION")
    print('=' * 60)

    documents = []
    total_words = 0

    for doc in included:
        md_path = Path(doc["path"])
        content = md_path.read_text(encoding='utf-8')

        # Get SharePoint URL from registry, fallback to placeholder
        source_url = url_lookup.get(doc["filename"], f"sharepoint://GGU/Bibliothek/{md_path.stem}.pdf")

        # Create document entry
        documents.append({
            "filename": doc["filename"],
            "content": content,
            "metadata": {
                "title": md_path.stem,
                "source": "sharepoint",
                "source_url": source_url,
            },
            "word_count": doc["word_count"],
        })
        total_words += doc["word_count"]

    print(f"\nReady to upload:")
    print(f"  Documents: {len(documents)}")
    print(f"  Total words: {total_words:,}")
    print(f"\nDocuments:")
    for doc in documents:
        has_url = not doc['metadata']['source_url'].startswith('sharepoint://')
        url_status = "[URL]" if has_url else "[NO URL]"
        print(f"  {url_status} {doc['filename']} ({doc['word_count']:,} words)")

    # Estimate time
    settings = get_settings()
    delay_per_doc = 3.0  # Standard plan
    estimated_minutes = (len(documents) * delay_per_doc) / 60
    print(f"\nEstimated upload time: ~{estimated_minutes:.1f} minutes")

    return documents


def upload_to_pinecone(documents: list[dict], dry_run: bool = True, clear_first: bool = False):
    """Upload documents to Pinecone Assistant."""
    from src.config import get_settings
    from src.pinecone import PineconeAssistant

    if not documents:
        print("No documents to upload.")
        return

    settings = get_settings()

    if not settings.pinecone_api_key:
        print("ERROR: PINECONE_API_KEY not set in environment")
        return

    print(f"\n{'=' * 60}")
    print(f"PINECONE UPLOAD {'(DRY RUN)' if dry_run else ''}")
    print('=' * 60)
    print(f"  Assistant: {settings.pinecone_assistant_name}")
    print(f"  Documents: {len(documents)}")
    if clear_first:
        print(f"  Clear existing: YES")

    if dry_run:
        print("\n[DRY RUN] Would upload the following documents:")
        if clear_first:
            print("  (Would first delete all existing files)")
        for doc in documents:
            print(f"  - {doc['filename']}")
        print("\nTo actually upload, run with --upload --confirm")
        if not clear_first:
            print("Add --clear to delete existing files first (prevents duplicates)")
        return

    print("\n[CONFIRMED] Proceeding with upload...")

    # Initialize assistant
    assistant = PineconeAssistant(
        api_key=settings.pinecone_api_key,
        assistant_name=settings.pinecone_assistant_name,
    )

    # Clear existing files if requested
    if clear_first:
        print("\nClearing existing files...")
        deleted = assistant.clear_all_files()
        print(f"  Deleted {deleted} existing files")

    # Upload progress callback
    def on_progress(uploaded, total, filename):
        print(f"  [{uploaded + 1}/{total}] Uploading {filename}...", end=" ", flush=True)

    print("\nStarting upload...")
    stats = assistant.upload_batch(documents, on_progress=on_progress)

    print(f"\n\n{'=' * 60}")
    print("UPLOAD COMPLETE")
    print('=' * 60)
    print(f"  Uploaded: {stats.uploaded}")
    print(f"  Failed: {stats.failed}")

    if stats.errors:
        print("\nErrors:")
        for error in stats.errors:
            print(f"  - {error}")


async def scan_norms(config_dir: Path) -> None:
    """Scan SharePoint and match documents to norm registry."""
    import asyncio
    from src.sharepoint.client import SharePointClient
    from src.sharepoint.documents import fetch_documents
    from src.indexing import NormMatcher

    registry_path = config_dir / "norms-registry.yaml"
    if not registry_path.exists():
        print(f"Registry not found: {registry_path}")
        return

    print(f"{'=' * 60}")
    print("SHAREPOINT NORM SCAN")
    print('=' * 60)

    # Initialize matcher
    matcher = NormMatcher(registry_path)
    print(f"Loaded {len(matcher.norms)} norms from registry")

    # Connect to SharePoint
    print("\nConnecting to SharePoint...")
    client = SharePointClient()

    if not await client.initialize():
        print("ERROR: Failed to connect to SharePoint")
        return

    print(f"Connected to: {client.settings.sharepoint_host}")
    print(f"Scanning folder: {client.settings.sharepoint_folder}")

    # Scan and match documents
    print("\nScanning for documents...")
    matches = []
    doc_count = 0

    async for doc in fetch_documents(client, file_extensions=['.pdf']):
        doc_count += 1
        match = matcher.match_document(doc.filename, doc.parent_path, doc.id, doc.web_url)
        if match:
            matches.append(match)
            print(f"  [MATCH] {doc.filename}")
            print(f"          -> {match.norm_id} (score: {match.score})")
        else:
            # Show non-matching docs at debug level
            pass

        # Progress indicator
        if doc_count % 50 == 0:
            print(f"  ... scanned {doc_count} documents, {len(matches)} matches ...")

    await client.close()

    print(f"\nScanned {doc_count} documents, found {len(matches)} matches")

    # Process matches and update registry
    print(f"\n{'=' * 60}")
    print("MATCHING RESULTS")
    print('=' * 60)

    result = matcher.process_matches(matches)

    print(f"\n  Total norms in registry: {result.total_norms}")
    print(f"  Found (active):          {result.found}")
    print(f"  Found (withdrawn only):  {result.withdrawn_only}")
    print(f"  Not found:               {result.not_found}")

    # Show details
    if result.matches:
        print(f"\n  Best matches:")
        for norm_key, match in sorted(result.matches.items()):
            status = "[WITHDRAWN]" if match.is_withdrawn else "[OK]"
            print(f"    {status} {norm_key}")
            print(f"           -> {match.filename}")

    # Show not found
    not_found_norms = [
        norm.id for norm_key, norm in matcher.norms.items()
        if norm_key not in result.matches
    ]
    if not_found_norms:
        print(f"\n  Not found in SharePoint:")
        for norm_id in sorted(not_found_norms):
            print(f"    [!!] {norm_id}")

    # Update registry
    print(f"\n{'=' * 60}")
    print("UPDATING REGISTRY")
    print('=' * 60)
    matcher.update_registry(result)
    print(f"Registry updated: {registry_path}")

    # Generate whitelist preview
    whitelist = matcher.generate_whitelist()
    print(f"\nGenerated whitelist with {len(whitelist)} documents")
    print("Run --prepare to see upload preview")


async def download_norms(config_dir: Path, downloads_dir: Path):
    """Download matched norm PDFs from SharePoint."""
    from src.sharepoint.client import SharePointClient
    from src.config import get_settings
    settings = get_settings()

    import yaml

    print("=" * 60)
    print("DOWNLOAD MATCHED NORMS")
    print("=" * 60)

    # Load registry
    registry_path = config_dir / "norms-registry.yaml"
    if not registry_path.exists():
        print(f"ERROR: Registry not found: {registry_path}")
        print("Run --scan-norms first.")
        return

    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = yaml.safe_load(f)

    # Find documents to download
    to_download = []
    for norm in registry.get('norms', []):
        status = norm.get('status', 'pending')
        if status in ('found', 'withdrawn_only'):
            item_id = norm.get('item_id')
            filename = norm.get('sharepoint_file')
            if item_id and filename:
                to_download.append({
                    'id': norm['id'],
                    'item_id': item_id,
                    'filename': filename,
                })
            elif not item_id:
                print(f"  [WARNING] {norm['id']}: No item_id - re-run --scan-norms")

    if not to_download:
        print("No documents to download. Run --scan-norms first.")
        return

    print(f"Found {len(to_download)} documents to download\n")

    # Connect to SharePoint
    print("Connecting to SharePoint...")
    client = SharePointClient(settings)
    if not await client.initialize():
        print("ERROR: Failed to connect to SharePoint")
        return

    print(f"Connected to: {client.settings.sharepoint_host}\n")

    # Ensure downloads directory exists
    downloads_dir.mkdir(exist_ok=True)

    # Download each file
    downloaded = 0
    skipped = 0
    failed = 0

    for doc in to_download:
        target_path = downloads_dir / doc['filename']

        # Skip if already downloaded
        if target_path.exists():
            print(f"  [SKIP] {doc['filename']} (already exists)")
            skipped += 1
            continue

        print(f"  [DOWNLOADING] {doc['filename']}...", end=" ", flush=True)

        try:
            content = await client.download_file(doc['item_id'])
            if content:
                with open(target_path, 'wb') as f:
                    f.write(content)
                print(f"OK ({len(content) // 1024} KB)")
                downloaded += 1
            else:
                print("FAILED (no content)")
                failed += 1
        except Exception as e:
            print(f"FAILED ({e})")
            failed += 1

    await client.close()

    print(f"\n{'=' * 60}")
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"  Downloaded: {downloaded}")
    print(f"  Skipped:    {skipped}")
    print(f"  Failed:     {failed}")

    if downloaded > 0 or skipped > 0:
        print(f"\nRun --extract to convert PDFs to markdown")


def main():
    parser = argparse.ArgumentParser(description="SharePoint PDF RAG Pipeline")
    parser.add_argument("--scan-norms", action="store_true", help="Scan SharePoint and match to norm registry")
    parser.add_argument("--download", action="store_true", help="Download matched PDFs from SharePoint")
    parser.add_argument("--extract", action="store_true", help="Extract PDFs to markdown")
    parser.add_argument("--validate", action="store_true", help="Validate extracted markdown")
    parser.add_argument("--prepare", action="store_true", help="Prepare upload batch (dry run)")
    parser.add_argument("--upload", action="store_true", help="Upload to Pinecone")
    parser.add_argument("--clear", action="store_true", help="Clear existing files before upload (prevents duplicates)")
    parser.add_argument("--confirm", action="store_true", help="Confirm upload (required with --upload)")

    args = parser.parse_args()

    # Default directories
    base_dir = Path(__file__).parent.parent
    downloads_dir = base_dir / "downloads"
    output_dir = base_dir / "output"
    config_dir = base_dir / "config"

    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)

    if args.scan_norms:
        import asyncio
        asyncio.run(scan_norms(config_dir))

    elif args.download:
        import asyncio
        asyncio.run(download_norms(config_dir, downloads_dir))

    elif args.extract:
        if not downloads_dir.exists():
            print(f"Downloads directory not found: {downloads_dir}")
            print("Place PDF files in the downloads/ folder first.")
            return
        extract_pdfs(downloads_dir, output_dir)

    elif args.validate:
        validate_markdown(output_dir)

    elif args.prepare:
        prepare_upload(output_dir, config_dir / "indexing.yaml")

    elif args.upload:
        documents = prepare_upload(output_dir, config_dir / "indexing.yaml")
        if documents:
            upload_to_pinecone(documents, dry_run=not args.confirm, clear_first=args.clear)

    else:
        parser.print_help()
        print("\nWorkflow:")
        print("  1. python scripts/pipeline.py --scan-norms     # Scan SharePoint, match norms")
        print("  2. python scripts/pipeline.py --download       # Download matched PDFs")
        print("  3. python scripts/pipeline.py --extract        # Extract PDFs to markdown")
        print("  4. python scripts/pipeline.py --validate       # Validate content quality")
        print("  5. python scripts/pipeline.py --prepare        # Preview upload")
        print("  6. python scripts/pipeline.py --upload --confirm  # Upload to Pinecone")
        print("")
        print("Re-upload with updated metadata (e.g., after adding web_url):")
        print("  python scripts/pipeline.py --upload --clear --confirm  # Clear & re-upload")


if __name__ == "__main__":
    main()
