# GGU Search Tools

Index GGU documentation for semantic search using Pinecone Assistant.

## Overview

This repository contains tools to index different documentation sources into Pinecone Assistants:

| Tool | Source | Technology | Target Assistant |
|------|--------|------------|------------------|
| **Web Crawler** | www.ggu-software.com (product pages) | JS/Bun + Firecrawl | `ggu-product-docs` |
| **Manual sync** *(lives in `ggu-manuals`)* | Markdown master of the user manuals | Python | `ggu-product-docs` |
| **SharePoint Indexer** | SharePoint PDF Library | Python + Docling | `ggu-techdoc-search-pdf` |

> **The user manuals are no longer crawled.** They have a Markdown master in the
> `ggu-manuals` repo, and that repo keeps the index in sync itself — on every merge to
> `main`, via `pipeline/sync-index.py` and the `index-sync` workflow (DEV-4862). Crawling
> them again would re-introduce exactly what DEV-4326 removed: a cookie banner, a "skip to
> content" link and a k15t support link in every single document — measured at 1,000
> characters of identical chrome per document across ~5,000 files.
>
> What the crawler still owns is the **product website**: 177 pages under
> `www.ggu-software.com` that have no Markdown master. Both sets live side by side in the
> same assistant and are told apart by the `source` metadata field, **not** by filename —
> one of the 177 crawled pages happens to carry a `__` in its name just like the manual
> pages do. The manual sync never deletes a file that lacks `source: manuals`.

## Architecture

```
                    ┌─────────────────────────────────────────┐
                    │           Pinecone Assistants           │
                    │  (chunk, embed, index, search - hosted) │
                    └─────────────────────────────────────────┘
                                       ▲
                    ┌──────────────────┴──────────────────┐
                    │                                      │
         ┌──────────┴──────────┐            ┌─────────────┴─────────────┐
         │    Web Crawler      │            │   SharePoint Indexer      │
         │    (JS/Bun)         │            │   (Python)                │
         └──────────┬──────────┘            └─────────────┬─────────────┘
                    │                                      │
         ┌──────────┴──────────┐            ┌─────────────┴─────────────┐
         │  Firecrawl SaaS     │            │  Docling (IBM) + OCR      │
         │  HTML → Markdown    │            │  PDF → Markdown           │
         └──────────┬──────────┘            └─────────────┬─────────────┘
                    │                                      │
         ┌──────────┴──────────┐            ┌─────────────┴─────────────┐
         │  GGU Websites       │            │  SharePoint Library       │
         │  - Product pages    │            │  - DIN Normen             │
         │    (177, no master) │            │  - Technical docs         │
         └─────────────────────┘            └───────────────────────────┘

   The user manuals reach the same assistant from the other side, without
   passing through this repo at all:

         ggu-manuals (Markdown master, 9,611 pages DE+EN)
              │  pipeline/sync-index.py — on every merge to main
              └────────────────────────────────►  ggu-product-docs
```

---

## Web Crawler (JS/Bun)

Crawl GGU websites and upload to Pinecone.

### Prerequisites

- [Bun](https://bun.sh) runtime
- [Firecrawl](https://firecrawl.dev) API key
- Pinecone account

### Setup

```bash
bun install
cp config.example.json config.json
# Edit config.json with your API keys
```

### Usage

```bash
# Crawl the product website
bun run crawl --source product-website

# Upload to Pinecone (skips what is already there)
bun run upload
```

### Configured Sources

| Source | URL | Description |
|--------|-----|-------------|
| `product-website` | www.ggu-software.com | Product pages (German), 177 pages — **the only source still crawled** |
| ~~`user-manuals`~~ | ~~manuals.ggu-software.com/ger/~~ | **Retired** (DEV-4326). Superseded by the Markdown export in `ggu-manuals`; the source domain itself is being redirected away (DEV-4665). The entry stays in `config.example.json` only so an existing `config.json` keeps parsing — do not run it. |

> ⚠️ `bun run upload --clear` wipes the assistant — **including the ~9,600 manual pages
> that this repo did not put there.** Rebuilding them is a two-and-a-half-hour job
> (`python pipeline/sync-index.py` over in `ggu-manuals`; the API accepts only about one
> write per second and pushing harder measurably delivers *less*). Use `bun run upload`
> without the flag: it skips whatever already exists.

---

## SharePoint Indexer (Python)

Extract DIN/EN/ISO norm PDFs from SharePoint, validate quality, and upload to Pinecone.

### Indexed Documents

The registry tracks all indexed documents:
- **Registry file**: [`sharepoint-indexer/config/norms-registry.yaml`](sharepoint-indexer/config/norms-registry.yaml)
- **Extracted markdown**: [`sharepoint-indexer/output/`](sharepoint-indexer/output/)

**Current status** (2026-02-04):
| Metric | Count |
|--------|-------|
| Total norms configured | 39 |
| Found & indexed | 38 |
| Withdrawn only | 1 |
| Total words | ~400,000 |

### Quick Start

```bash
cd sharepoint-indexer
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

### Pipeline Workflow

The indexer uses a multi-stage pipeline to ensure quality:

```
┌─────────────┐    ┌──────────┐    ┌─────────┐    ┌─────────┐    ┌────────┐
│ scan-norms  │───►│ download │───►│ extract │───►│ prepare │───►│ upload │
└─────────────┘    └──────────┘    └─────────┘    └─────────┘    └────────┘
     │                  │               │              │              │
     ▼                  ▼               ▼              ▼              ▼
  Registry          PDFs in        Markdown        Validate      Pinecone
  updated          downloads/      in output/      quality       Assistant
```

#### Stage 1: Scan Norms
```bash
python scripts/pipeline.py --scan-norms
```
- Scans SharePoint library for documents matching configured norms
- Updates `config/norms-registry.yaml` with found files
- Uses intelligent matching (handles version dates, withdrawn status)

#### Stage 2: Download
```bash
python scripts/pipeline.py --download
```
- Downloads matched PDFs from SharePoint to `downloads/`
- Uses item IDs from registry for reliable access

#### Stage 3: Extract
```bash
python scripts/pipeline.py --extract
```
- Converts PDFs to Markdown using Docling (IBM)
- Includes OCR for scanned documents (RapidOCR)
- Output saved to `output/`

#### Stage 4: Prepare (Validate)
```bash
python scripts/pipeline.py --prepare
```
- Validates extracted documents
- Checks for OCR issues, empty content, glyph encoding problems
- Reports word counts and quality metrics

#### Stage 5: Upload
```bash
python scripts/pipeline.py --upload           # Dry run
python scripts/pipeline.py --upload --confirm # Actually upload
```
- Uploads validated documents to Pinecone Assistant
- Only uploads documents marked in registry filter

### Adding New Documents

> **Fastest path — Claude Code skill `add-norm-to-search`.** It locates the norm
> PDF in SharePoint (read-only), writes the registry entry, downloads, and uploads
> to the PDF assistant. See
> `infra/ggu-dev-tools/claude-code/skills/add-norm-to-search/` (SKILL.md +
> references/workflow.md). The manual steps below are the underlying mechanics.

> **Two assistants:** `--upload-pdf` feeds `ggu-techdoc-search-pdf` (raw PDFs,
> page-aware — this is the corpus behind the `ggu-techdoc-search` MCP and
> connie.ggu-connect.com). `--upload` feeds `ggu-techdoc-search` (docling markdown).
> `--upload-pdf` is delta-aware (`--only-missing`); the markdown `--upload` is NOT —
> never run a blanket `--upload` to add a single norm (it duplicates the corpus).
> docling 2.98 note: the default parser segfaults on some PDFs — use
> `enable_ocr=False` + `PyPdfiumDocumentBackend`.

1. **Add norm to filter config** (`config/norms-filter.yaml`):
   ```yaml
   norms:
     - id: "DIN 18196"
       description: "Bodenklassifikation"
       category: geotechnical
       priority: high
   ```

2. **Run the pipeline**:
   ```bash
   python scripts/pipeline.py --scan-norms
   python scripts/pipeline.py --download
   python scripts/pipeline.py --extract
   python scripts/pipeline.py --prepare
   python scripts/pipeline.py --upload --confirm
   ```

3. **Update tracking**:
   ```bash
   python scripts/update_registry_indexed.py
   ```

4. **Commit changes**:
   ```bash
   git add config/norms-registry.yaml output/
   git commit -m "Add new indexed documents"
   git push
   ```

### Features

- **Docling (IBM)**: High-quality PDF extraction with OCR
- **Quality Validation**: Detect corrupted PDFs (glyph encoding issues)
- **SharePoint Integration**: Microsoft Graph API for document access
- **Registry Tracking**: Full audit trail of indexed documents

---

## Claude Code Integration

After uploading, documentation is searchable in Claude Code via MCP servers.

### Available MCP Servers

| Server | Assistant | Content | Documents |
|--------|-----------|---------|-----------|
| `ggu-public-docs` | `ggu-product-docs` (EU) | Product website + user manuals | ~9,800 pages |
| `ggu-techdoc-search` | `ggu-techdoc-search-pdf` (EU) | DIN/EN/ISO norms (internal) | 39 norms |

Both assistants live in the EU region, so the host is `prod-eu-data`, **not**
`prod-1-data`. The product assistant was rebuilt from the Markdown master under the new
name `ggu-product-docs` (DEV-4326). The old `ggu-software-public-search` on `prod-1-data`
still answers — with a January 2026 crawl of the retired `manuals.ggu-software.com`, so
its links are dead. Pointing every consumer at the new one and switching the old one off
is DEV-4864.

### Setup

1. **Get the API Key** from Bitwarden:
   - [Pinecone Read-Only API Key](https://vault.bitwarden.eu/#/vault?action=view&itemId=4c7df23b-bf77-43dd-8d24-b3d40159dc1a)

2. **Add to your `.mcp.json`:**

   ```json
   {
     "mcpServers": {
       "ggu-public-docs": {
         "type": "http",
         "url": "https://prod-eu-data.ke.pinecone.io/mcp/assistants/ggu-product-docs",
         "headers": {
           "Authorization": "Bearer YOUR_PINECONE_API_KEY"
         }
       },
       "ggu-techdoc-search": {
         "type": "http",
         "url": "https://prod-eu-data.ke.pinecone.io/mcp/assistants/ggu-techdoc-search-pdf",
         "headers": {
           "Authorization": "Bearer YOUR_PINECONE_API_KEY"
         }
       }
     }
   }
   ```

3. **Restart Claude Code** to load the MCP servers.

### Usage Examples

**Public Documentation** (`ggu-public-docs`):
```
Search documentation: "GGU-RETAIN Normen"
Search documentation: "BIM Export GGU-CONNECT"
```

**Technical Norms** (`ggu-techdoc-search`):
```
Search technical docs: "Wassergehalt bestimmen nach Norm"
Search technical docs: "Erddruckberechnung DIN 4085"
Search technical docs: "Korngrößenverteilung Siebanalyse"
```

### Indexed Norms

The following categories of norms are indexed in `ggu-techdoc-search`:

| Category | Examples |
|----------|----------|
| **Soil Mechanics** | DIN 18196, DIN EN ISO 14688, DIN EN ISO 17892 |
| **Foundation Design** | DIN 1054, DIN 4017, DIN 4019, EC 7 |
| **Earth Pressure** | DIN 4085, DIN 4084 |
| **Field Testing** | DIN EN ISO 22476 (CPT, SPT, Vane) |
| **Lab Testing** | DIN 18122-18141 (Proctor, Permeability, Shear) |

Full list: [`sharepoint-indexer/config/norms-registry.yaml`](sharepoint-indexer/config/norms-registry.yaml)

---

## Cost Estimation

| Service | Cost |
|---------|------|
| Firecrawl | ~6,000 credits for full crawl |
| Pinecone Assistant | Free tier (100MB storage) |

---

## Troubleshooting

### "No files found" in Claude Code
Files may still be processing. Wait a few minutes after upload.

### Crawl timeout
Large sites may take longer. The script polls for up to 10 minutes.

### Upload failures
Check API keys in config.json or .env file.
