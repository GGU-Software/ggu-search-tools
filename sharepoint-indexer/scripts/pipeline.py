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
import re
import time
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))


def embed_url_in_sections(content: str, source_url: str, norm_name: str) -> str:
    """
    Embed source URL after each major heading in the document.

    This ensures the URL appears in more Pinecone chunks, not just the first one.
    URLs are injected after ## and ### headings as a compact reference block.

    Args:
        content: Original markdown content
        source_url: SharePoint URL to embed
        norm_name: Human-readable norm name for context

    Returns:
        Content with URLs embedded after each section heading
    """
    # Compact reference format (single line to minimize document bloat)
    # Using text marker instead of emoji for better encoding compatibility
    url_ref = f"\n> **Quelle:** {norm_name} - [Original in SharePoint]({source_url})\n"

    # Pattern to match ## and ### headings (but not #### or deeper)
    # Captures the full heading line including any trailing whitespace
    heading_pattern = re.compile(r'^(#{2,3}\s+[^\n]+)(\n)', re.MULTILINE)

    # Insert URL reference after each heading
    def insert_ref(match):
        heading = match.group(1)
        newline = match.group(2)
        return heading + newline + url_ref

    content_with_urls = heading_pattern.sub(insert_ref, content)

    # Also add header at document start for searches that match the beginning
    doc_header = f"---\n**Dokument:** {norm_name}\n**SharePoint:** {source_url}\n---\n\n"

    return doc_header + content_with_urls

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

        # Embed source URL throughout the document (so it appears in more Pinecone chunks)
        # URLs are injected after each ## and ### heading, plus a header at the top
        has_real_url = not source_url.startswith('sharepoint://')
        if has_real_url:
            # Extract norm name from filename for better context
            norm_name = md_path.stem.split('_')[0].replace('-', ' ').strip()
            content_with_url = embed_url_in_sections(content, source_url, norm_name)
        else:
            content_with_url = content

        # Create document entry
        documents.append({
            "filename": doc["filename"],
            "content": content_with_url,
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
        url_status = "[URL embedded]" if has_url else "[NO URL]"
        print(f"  {url_status} {doc['filename']} ({doc['word_count']:,} words)")

    # Estimate time
    settings = get_settings()
    delay_per_doc = 3.0  # Standard plan
    estimated_minutes = (len(documents) * delay_per_doc) / 60
    print(f"\nEstimated upload time: ~{estimated_minutes:.1f} minutes")

    return documents


def upload_pdfs_to_pinecone(
    downloads_dir: Path,
    registry_path: Path,
    assistant_name: str,
    dry_run: bool = True,
    clear_first: bool = False,
    multimodal: bool = False,
    only_missing: bool = False,
):
    """
    Upload raw PDFs directly to a Pinecone Assistant.

    Unlike `upload_to_pinecone` (which uploads pre-extracted markdown),
    this sends the original PDF files. Pinecone parses them server-side
    and preserves page boundaries, so context responses include
    `reference.pages` for every snippet.

    Args:
        downloads_dir: Directory containing downloaded *.pdf files
        registry_path: Path to norms-registry.yaml (provides web_url per file)
        assistant_name: Pinecone assistant to upload to
        dry_run: If True, list files only without uploading
        clear_first: If True, delete all existing files in the assistant first
    """
    import yaml
    from src.config import get_settings
    from src.pinecone import PineconeAssistant

    if not downloads_dir.exists():
        print(f"Downloads directory not found: {downloads_dir}")
        print("Run --download first to fetch PDFs from SharePoint.")
        return

    if not registry_path.exists():
        print(f"Registry not found: {registry_path}")
        return

    # Build file -> web_url lookup; restrict to norms marked `indexed: true`
    with open(registry_path, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    url_by_file = {}
    for norm in registry.get("norms", []):
        pdf_file = norm.get("sharepoint_file")
        web_url = norm.get("web_url")
        indexed = norm.get("indexed", False)
        if pdf_file and web_url and indexed:
            url_by_file[pdf_file] = web_url

    # Filter local PDFs to the ones present in the registry + indexed
    pdfs = sorted(
        p for p in downloads_dir.glob("*.pdf") if p.name in url_by_file
    )

    # Size sanity check (Pinecone standard plan: 100 MB per PDF)
    MAX_MB = 100
    oversized = [p for p in pdfs if p.stat().st_size > MAX_MB * 1024 * 1024]

    print(f"\n{'=' * 60}")
    print(f"PDF UPLOAD {'(DRY RUN)' if dry_run else ''}")
    print(f"{'=' * 60}")
    print(f"  Assistant: {assistant_name}")
    print(f"  Source:    {downloads_dir}")
    print(f"  PDFs:      {len(pdfs)}")
    if clear_first:
        print(f"  Clear existing: YES")

    if oversized:
        print(f"\n  [!!] {len(oversized)} PDF(s) exceed {MAX_MB} MB and will FAIL:")
        for p in oversized:
            mb = p.stat().st_size / (1024 * 1024)
            print(f"    - {p.name} ({mb:.1f} MB)")

    ready = [p for p in pdfs if p not in oversized]
    if not ready:
        print("\nNothing to upload.")
        return

    settings = get_settings()
    if not settings.pinecone_api_key:
        print("\nERROR: PINECONE_API_KEY not set in environment")
        return

    assistant = PineconeAssistant(
        api_key=settings.pinecone_api_key,
        assistant_name=assistant_name,
    )

    # Peek at current assistant state so dry-run preview is accurate.
    # In --clear_first mode we treat it as "everything will be deleted".
    skip_names: set[str] = set()
    purge_entries: list = []  # (file_id, name) — non-Available ghosts to drop
    if not clear_first:
        existing = assistant.list_files()
        for f in existing:
            name = getattr(f, "name", None) or (f.get("name") if isinstance(f, dict) else None)
            status = getattr(f, "status", None) or (f.get("status") if isinstance(f, dict) else None)
            file_id = getattr(f, "id", None) or (f.get("id") if isinstance(f, dict) else None)
            if not name:
                continue
            if status == "Available":
                skip_names.add(name)
            elif file_id:
                purge_entries.append((file_id, name, status))

    # Apply --only-missing narrowing before the preview
    targets = ready
    if only_missing:
        targets = [p for p in ready if p.name not in skip_names]

    print(f"\nFiles to upload:")
    total_mb = 0.0
    for p in targets:
        mb = p.stat().st_size / (1024 * 1024)
        total_mb += mb
        print(f"  [{mb:5.1f} MB] {p.name}")
    print(f"\n  Total:  {total_mb:.1f} MB across {len(targets)} file(s)")
    if skip_names:
        print(f"  Skipped (already Available): {len(skip_names)}")
    if purge_entries:
        print(f"  Will purge (not Available):  {len(purge_entries)}")
        for _, n, s in purge_entries:
            print(f"    [{s}] {n}")

    if dry_run:
        print("\n[DRY RUN] Re-run with --confirm to actually upload.")
        if not clear_first and not only_missing:
            print("Add --clear to delete existing files first (prevents duplicates).")
        return

    print("\n[CONFIRMED] Proceeding with upload...")

    if clear_first:
        print("\nClearing existing files...")
        deleted = assistant.clear_all_files()
        print(f"  Deleted {deleted} existing files")
        skip_names = set()
    elif purge_entries:
        # Drop ProcessingFailed / transient entries so a re-upload can replace them
        purged = 0
        for file_id, _, _ in purge_entries:
            if assistant.delete_file(file_id):
                purged += 1
        print(f"\nPurged {purged} non-Available entries.")

    uploaded = 0
    skipped = 0
    failed = 0
    errors: list[str] = []

    # Optional narrowing: only upload files NOT currently in the assistant
    targets = ready
    if only_missing:
        targets = [p for p in ready if p.name not in skip_names]
        print(f"\n--only-missing filter: {len(targets)} PDFs remaining (was {len(ready)}).")

    mode_label = "multimodal" if multimodal else "standard"
    print(
        f"\nStarting upload ({assistant.upload_delay:.1f}s delay per file, {mode_label} mode)..."
    )
    for i, pdf in enumerate(targets, 1):
        if pdf.name in skip_names:
            print(f"  [{i}/{len(targets)}] {pdf.name}... SKIP (already Available)")
            skipped += 1
            continue

        print(f"  [{i}/{len(targets)}] {pdf.name}...", end=" ", flush=True)
        result = assistant.upload_pdf(
            pdf,
            metadata={
                "title": pdf.stem,
                "source": "sharepoint",
                "source_url": url_by_file[pdf.name],
            },
            multimodal=multimodal,
        )
        if result.success:
            uploaded += 1
            print("OK")
        else:
            failed += 1
            errors.append(f"{pdf.name}: {result.error}")
            print(f"FAIL ({result.error})")

        if i < len(targets):
            time.sleep(assistant.upload_delay)

    print(f"\n{'=' * 60}")
    print("UPLOAD COMPLETE")
    print(f"{'=' * 60}")
    print(f"  Uploaded: {uploaded}")
    print(f"  Skipped:  {skipped}")
    print(f"  Failed:   {failed}")
    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  - {e}")


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


async def resolve_registry_paths(config_dir: Path) -> int:
    """
    Fill missing `item_id` entries in norms-registry.yaml using the
    `sharepoint_path` + `sharepoint_file` fields.

    This is the deterministic counterpart to `scan_norms`: the scanner's
    fuzzy matcher occasionally misses documents (DGGT books in non-standard
    subfolders, non-DIN prefixes, etc.). Whenever a registry entry carries
    an explicit path+filename, we can look the item up directly via Graph
    API and record the resolved `item_id` + `web_url`.

    Run automatically at the end of `--scan-norms`; also available as
    `--resolve-paths` for targeted reruns.

    Returns the number of entries newly resolved.
    """
    from src.sharepoint.client import SharePointClient
    import yaml

    registry_path = config_dir / "norms-registry.yaml"
    if not registry_path.exists():
        print(f"Registry not found: {registry_path}")
        return 0

    with open(registry_path, "r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    # Candidates: entries with explicit path+file but no item_id
    candidates = []
    for norm in registry.get("norms", []):
        if norm.get("item_id"):
            continue
        path = norm.get("sharepoint_path")
        fname = norm.get("sharepoint_file")
        if path and fname:
            candidates.append(norm)

    if not candidates:
        print("No registry entries need path resolution.")
        return 0

    print(f"\n{'=' * 60}")
    print("RESOLVE REGISTRY PATHS")
    print('=' * 60)
    print(f"Candidates (have path+file, missing item_id): {len(candidates)}")
    for n in candidates:
        print(f"  - {n['id']:30s}  {n['sharepoint_path']}/{n['sharepoint_file']}")

    print("\nConnecting to SharePoint...")
    client = SharePointClient()
    if not await client.initialize():
        print("ERROR: Failed to connect to SharePoint")
        return 0

    resolved = 0
    not_found = 0
    for n in candidates:
        result = await client.resolve_by_path(n["sharepoint_path"], n["sharepoint_file"])
        if result and result.get("id"):
            n["item_id"] = result["id"]
            if result.get("webUrl") and not n.get("web_url"):
                n["web_url"] = result["webUrl"]
            n["status"] = "found"
            # Registry entries with explicit path+file are author-curated;
            # once the file is confirmed to exist, mark it indexable.
            # Exclusion of specific docs belongs in indexing.yaml, not here.
            n["indexed"] = True
            resolved += 1
            print(f"  [OK]  {n['id']}  -> {result['id'][:20]}...")
        else:
            not_found += 1
            print(f"  [--]  {n['id']}  not found at declared path")

    await client.close()

    if resolved:
        with open(registry_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(registry, f, allow_unicode=True, sort_keys=False)
        print(f"\nRegistry updated: {registry_path}")

    print(f"\nResolved: {resolved}   Not found: {not_found}")
    return resolved


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

    # Final pass: resolve any registry entries that have explicit path+file
    # but were still missed by the fuzzy matcher. Prevents DGGT-book-style
    # gaps from persisting across scans.
    await resolve_registry_paths(config_dir)

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
    parser.add_argument("--scan-norms", action="store_true", help="Scan SharePoint and match to norm registry (includes --resolve-paths as last step)")
    parser.add_argument("--resolve-paths", action="store_true", help="Fill missing item_ids in registry by direct path lookup (for entries with sharepoint_path+file)")
    parser.add_argument("--download", action="store_true", help="Download matched PDFs from SharePoint")
    parser.add_argument("--extract", action="store_true", help="Extract PDFs to markdown")
    parser.add_argument("--validate", action="store_true", help="Validate extracted markdown")
    parser.add_argument("--prepare", action="store_true", help="Prepare upload batch (dry run)")
    parser.add_argument("--upload", action="store_true", help="Upload markdown to Pinecone (legacy path)")
    parser.add_argument("--upload-pdf", action="store_true", help="Upload raw PDFs to Pinecone (preserves pages)")
    parser.add_argument("--assistant", default="ggu-techdoc-search-pdf", help="Target Pinecone assistant for --upload-pdf")
    parser.add_argument("--multimodal", action="store_true", help="Enable multimodal processing (OCR + image captioning, needed for scanned PDFs)")
    parser.add_argument("--only-missing", action="store_true", help="Upload only PDFs not already Available in the assistant")
    parser.add_argument("--clear", action="store_true", help="Clear existing files before upload (prevents duplicates)")
    parser.add_argument("--confirm", action="store_true", help="Confirm upload (required with --upload/--upload-pdf)")

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

    elif args.resolve_paths:
        import asyncio
        asyncio.run(resolve_registry_paths(config_dir))

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

    elif args.upload_pdf:
        upload_pdfs_to_pinecone(
            downloads_dir=downloads_dir,
            registry_path=config_dir / "norms-registry.yaml",
            assistant_name=args.assistant,
            dry_run=not args.confirm,
            clear_first=args.clear,
            multimodal=args.multimodal,
            only_missing=args.only_missing,
        )

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
        print("")
        print("PDF-based (parallel) assistant for page-aware retrieval:")
        print("  python scripts/pipeline.py --upload-pdf                       # Preview upload")
        print("  python scripts/pipeline.py --upload-pdf --confirm             # Upload PDFs")
        print("  python scripts/pipeline.py --upload-pdf --clear --confirm     # Clear & re-upload")
        print("  python scripts/pipeline.py --upload-pdf --assistant <name>    # Custom target")


if __name__ == "__main__":
    main()
