# GGU Search Tools

Index GGU documentation for semantic search using Pinecone Assistant.

## Overview

This repository contains tools to index different documentation sources into Pinecone Assistants:

| Tool | Source | Technology | Target Assistant |
|------|--------|------------|------------------|
| **Web Crawler** | ggu-software.com, manuals | JS/Bun + Firecrawl | `ggu-software-public-search` |
| **SharePoint Indexer** | SharePoint PDF Library | Python + Docling | `ggu-techdoc-search` |

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
         │  - User manuals     │            │  - Technical docs         │
         └─────────────────────┘            └───────────────────────────┘
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
# Crawl websites
bun run crawl
bun run crawl --source product-website
bun run crawl --source user-manuals

# Upload to Pinecone
bun run upload
bun run upload --clear  # Clear existing first

# Full sync
bun run sync
```

### Configured Sources

| Source | URL | Description |
|--------|-----|-------------|
| `product-website` | www.ggu-software.com | Product pages (German) |
| `user-manuals` | manuals.ggu-software.com/ger/ | User documentation (~5,900 pages) |

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
| `ggu-public-docs` | `ggu-software-public-search` | Public website, user manuals | ~6,000 pages |
| `ggu-techdoc-search` | `ggu-techdoc-search` | DIN/EN/ISO norms (internal) | 39 norms |

### Setup

1. **Get the API Key** from Bitwarden:
   - [Pinecone Read-Only API Key](https://vault.bitwarden.eu/#/vault?action=view&itemId=4c7df23b-bf77-43dd-8d24-b3d40159dc1a)

2. **Add to your `.mcp.json`:**

   ```json
   {
     "mcpServers": {
       "ggu-public-docs": {
         "type": "http",
         "url": "https://prod-1-data.ke.pinecone.io/mcp/assistants/ggu-software-public-search",
         "headers": {
           "Authorization": "Bearer YOUR_PINECONE_API_KEY"
         }
       },
       "ggu-techdoc-search": {
         "type": "http",
         "url": "https://prod-1-data.ke.pinecone.io/mcp/assistants/ggu-techdoc-search",
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
