/**
 * Crawl GGU documentation using Firecrawl API
 *
 * This script crawls the GGU product website and user manuals,
 * converting HTML to Markdown and preserving source URLs.
 *
 * Usage:
 *   bun run crawl
 *   bun run scripts/crawl.ts
 *   bun run scripts/crawl.ts --source product-website
 */

import { existsSync, mkdirSync, writeFileSync, readFileSync } from "fs";
import { join } from "path";

// ============================================================================
// Types
// ============================================================================

interface Config {
  firecrawl: {
    apiKey: string;
  };
  pinecone: {
    apiKey: string;
    assistantName: string;
  };
  sources: Source[];
  output: {
    directory: string;
  };
}

interface Source {
  name: string;
  url: string;
  excludePaths?: string[];
  includePaths?: string[];
  limit?: number;
}

interface CrawlResponse {
  success: boolean;
  id?: string;
  status?: string;
  total?: number;
  completed?: number;
  data?: CrawlPage[];
  error?: string;
}

interface CrawlPage {
  markdown?: string;
  html?: string;
  metadata?: {
    title?: string;
    description?: string;
    sourceURL?: string;
    language?: string;
  };
}

// ============================================================================
// Config
// ============================================================================

function loadConfig(): Config {
  const configPath = join(import.meta.dir, "..", "config.json");

  if (!existsSync(configPath)) {
    console.error("Error: config.json not found");
    console.error("Copy config.example.json to config.json and add your API keys");
    process.exit(1);
  }

  return JSON.parse(readFileSync(configPath, "utf-8"));
}

// ============================================================================
// Firecrawl API
// ============================================================================

const FIRECRAWL_API = "https://api.firecrawl.dev/v1";

async function startCrawl(
  apiKey: string,
  source: Source
): Promise<string> {
  console.log(`\nStarting crawl for: ${source.name}`);
  console.log(`  URL: ${source.url}`);
  console.log(`  Limit: ${source.limit || "unlimited"}`);

  const response = await fetch(`${FIRECRAWL_API}/crawl`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      url: source.url,
      excludePaths: source.excludePaths,
      includePaths: source.includePaths,
      limit: source.limit,
      scrapeOptions: {
        formats: ["markdown"],
        onlyMainContent: true,
      },
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Firecrawl API error: ${response.status} - ${error}`);
  }

  const result = (await response.json()) as CrawlResponse;

  if (!result.success || !result.id) {
    throw new Error(`Crawl failed: ${result.error || "Unknown error"}`);
  }

  console.log(`  Crawl started with ID: ${result.id}`);
  return result.id;
}

async function pollCrawlStatus(
  apiKey: string,
  crawlId: string
): Promise<CrawlPage[]> {
  const maxAttempts = 600; // 10 minutes max
  const pollInterval = 2000; // 2 seconds

  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    const response = await fetch(`${FIRECRAWL_API}/crawl/${crawlId}`, {
      headers: {
        Authorization: `Bearer ${apiKey}`,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Status check failed: ${response.status} - ${error}`);
    }

    const result = (await response.json()) as CrawlResponse;

    if (result.status === "completed") {
      console.log(`  Crawl completed: ${result.total} pages`);
      return result.data || [];
    }

    if (result.status === "failed") {
      throw new Error(`Crawl failed: ${result.error}`);
    }

    // Show progress
    const progress = result.completed || 0;
    const total = result.total || "?";
    process.stdout.write(`\r  Progress: ${progress}/${total} pages...`);

    await new Promise((resolve) => setTimeout(resolve, pollInterval));
  }

  throw new Error("Crawl timed out");
}

// ============================================================================
// Output
// ============================================================================

function sanitizeFilename(url: string): string {
  return url
    .replace(/^https?:\/\//, "")
    .replace(/[^a-zA-Z0-9-_.]/g, "_")
    .substring(0, 200);
}

function savePages(
  pages: CrawlPage[],
  sourceName: string,
  outputDir: string
): void {
  const sourceDir = join(outputDir, sourceName);

  if (!existsSync(sourceDir)) {
    mkdirSync(sourceDir, { recursive: true });
  }

  let savedCount = 0;

  for (const page of pages) {
    if (!page.markdown || !page.metadata?.sourceURL) {
      continue;
    }

    const filename = sanitizeFilename(page.metadata.sourceURL) + ".md";
    const filepath = join(sourceDir, filename);

    // Add frontmatter with metadata
    const content = `---
title: ${JSON.stringify(page.metadata.title || "Untitled")}
url: ${JSON.stringify(page.metadata.sourceURL)}
description: ${JSON.stringify(page.metadata.description || "")}
---

${page.markdown}
`;

    writeFileSync(filepath, content, "utf-8");
    savedCount++;
  }

  console.log(`  Saved ${savedCount} markdown files to ${sourceDir}`);
}

// ============================================================================
// Main
// ============================================================================

async function main() {
  console.log("=".repeat(60));
  console.log("GGU Documentation Crawler");
  console.log("=".repeat(60));

  const config = loadConfig();

  // Parse command line args
  const args = process.argv.slice(2);
  const sourceFilter = args.includes("--source")
    ? args[args.indexOf("--source") + 1]
    : null;

  // Filter sources if specified
  const sources = sourceFilter
    ? config.sources.filter((s) => s.name === sourceFilter)
    : config.sources;

  if (sources.length === 0) {
    console.error(`No sources found${sourceFilter ? ` matching "${sourceFilter}"` : ""}`);
    process.exit(1);
  }

  console.log(`\nSources to crawl: ${sources.map((s) => s.name).join(", ")}`);

  // Ensure output directory exists
  const outputDir = config.output.directory;
  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }

  // Crawl each source
  for (const source of sources) {
    try {
      const crawlId = await startCrawl(config.firecrawl.apiKey, source);
      const pages = await pollCrawlStatus(config.firecrawl.apiKey, crawlId);
      savePages(pages, source.name, outputDir);
    } catch (error) {
      console.error(`\nError crawling ${source.name}:`, error);
    }
  }

  console.log("\n" + "=".repeat(60));
  console.log("Crawl complete!");
  console.log(`Output directory: ${outputDir}`);
  console.log("=".repeat(60));
}

main().catch(console.error);
