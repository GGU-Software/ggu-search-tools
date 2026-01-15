# GGU Search Tools

Crawl and index GGU documentation for semantic search using Firecrawl and Pinecone Assistant.

## Architecture

```
[Firecrawl SaaS]          - Crawl websites, convert HTML to Markdown
        |
        v
[Local Markdown Files]    - Stored in ./output/
        |
        v
[Pinecone Assistant]      - Upload, chunk, embed, index (hosted)
        |
        v
[Pinecone MCP Server]     - Query via Claude Code / Connie
```

## Prerequisites

- [Bun](https://bun.sh) runtime
- [Firecrawl](https://firecrawl.dev) API key
- [Pinecone](https://pinecone.io) account with Assistant

## Setup

1. **Install dependencies:**
   ```bash
   bun install
   ```

2. **Create config.json:**
   ```bash
   cp config.example.json config.json
   ```

3. **Add your API keys to config.json:**
   ```json
   {
     "firecrawl": {
       "apiKey": "fc-your-api-key"
     },
     "pinecone": {
       "apiKey": "pcsk_your-api-key",
       "assistantName": "ggu-software-public-search"
     }
   }
   ```

## Usage

### Crawl Documentation

Crawl all configured sources:
```bash
bun run crawl
```

Crawl a specific source:
```bash
bun run crawl --source product-website
bun run crawl --source user-manuals
```

### Upload to Pinecone

Upload all crawled files:
```bash
bun run upload
```

Upload specific source:
```bash
bun run upload --source product-website
```

Clear existing files and re-upload:
```bash
bun run upload --clear
```

### Full Sync

Crawl and upload in one command:
```bash
bun run sync
```

## Configured Sources

| Source | URL | Description |
|--------|-----|-------------|
| `product-website` | www.ggu-software.com | Product pages (German, excludes /en/) |
| `user-manuals` | manuals.ggu-software.com/ger/ | User documentation (~5,900 pages) |

## Output Structure

```
output/
  product-website/
    www.ggu-software.com_geotechnik-software_....md
    ...
  user-manuals/
    manuals.ggu-software.com_ger_ggu-retain_....md
    ...
```

Each markdown file includes frontmatter with metadata:
```yaml
---
title: "Page Title"
url: "https://www.ggu-software.com/..."
description: "Page description"
---
```

## Claude Code Integration

After uploading, the documentation is searchable in Claude Code via the `ggu-public-docs` MCP server:

```json
// .mcp.json
{
  "mcpServers": {
    "ggu-public-docs": {
      "type": "http",
      "url": "https://prod-1-data.ke.pinecone.io/mcp/assistants/ggu-software-public-search",
      "headers": {
        "Authorization": "Bearer ${PINECONE_API_KEY}"
      }
    }
  }
}
```

## Update Process

When website content changes:

1. Re-crawl the updated source:
   ```bash
   bun run crawl --source product-website
   ```

2. Re-upload to Pinecone:
   ```bash
   bun run upload --clear
   ```

## Cost Estimation

| Service | Cost |
|---------|------|
| Firecrawl | ~6,000 credits for full crawl |
| Pinecone Assistant | Free tier (100MB storage) |

## Troubleshooting

### "No files found" error in Claude Code
Files may still be processing. Wait a few minutes after upload.

### Crawl timeout
Large sites may take longer. The script polls for up to 10 minutes.

### Upload failures
Check Pinecone API key and assistant name in config.json.
