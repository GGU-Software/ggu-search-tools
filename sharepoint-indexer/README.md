# SharePoint PDF Indexer

Extract PDFs from SharePoint, convert to Markdown, and upload to Pinecone Assistant.

## Architecture

```
[SharePoint Library]     - Source: GGU/Bibliothek (DIN Normen, etc.)
        |
        v
[PDF Extraction]         - Docling (IBM) with OCR
        |
        v
[Quality Validation]     - Detect corrupted PDFs (glyph encoding issues)
        |
        v
[Markdown Files]         - Structured text with headings, tables
        |
        v
[Pinecone Assistant]     - Upload, chunk, embed, index (hosted)
```

## Setup

1. **Create virtual environment:**
   ```bash
   cd sharepoint-indexer
   python -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

## Configuration

Create a `.env` file with:

```env
# Azure AD (SharePoint access)
SHAREPOINT_CLIENT_ID=your-client-id
SHAREPOINT_CLIENT_SECRET=your-client-secret
SHAREPOINT_TENANT_ID=your-tenant-id

# SharePoint location
SHAREPOINT_HOST=ggu.sharepoint.de
SHAREPOINT_SITE=sites/GGUTeamSite
SHAREPOINT_DRIVE=GGU
SHAREPOINT_FOLDER=Bibliothek

# Pinecone (uses shared config from parent)
PINECONE_API_KEY=your-pinecone-key
PINECONE_ASSISTANT_NAME=ggu-techdoc-search
```

## Usage

### Test Extraction

```bash
python scripts/test_extraction.py
```

### Test Chunking

```bash
python scripts/test_chunking.py
```

## Module Structure

```
src/
  config.py              # Settings from environment
  extraction/            # PDF → Markdown
    pdf_extractor.py     # Docling integration
    validator.py         # Quality checks
    models.py
  chunking/              # Section-aware chunking
    section_chunker.py
    models.py
  sharepoint/            # SharePoint Graph API
    client.py
    documents.py
    models.py
  pinecone/              # Pinecone Assistant upload
    (coming soon)
```

## Quality Validation

The validator detects problematic PDFs:

| Issue | Description | Action |
|-------|-------------|--------|
| `glyph_encoding` | PDF uses font glyph names instead of text | Skip indexing |
| `low_text_ratio` | Very little extractable text | Warning |
| `empty` | No meaningful content | Skip indexing |

Documents with critical issues are logged but not indexed to avoid polluting search results.
