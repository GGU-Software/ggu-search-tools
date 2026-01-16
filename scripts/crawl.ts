/**
 * Crawl GGU documentation using Firecrawl API
 *
 * This script crawls the GGU product website and user manuals,
 * converting HTML to Markdown and preserving source URLs.
 *
 * Features:
 * - Checkpoint/Resume: Saves progress, can resume after interruption
 * - Rate limiting: Respects API limits
 *
 * Usage:
 *   bun run crawl
 *   bun run scripts/crawl.ts
 *   bun run scripts/crawl.ts --source product-website
 *   bun run scripts/crawl.ts --source manuals
 *   bun run scripts/crawl.ts --resume  # Resume interrupted crawl
 */

import { existsSync, mkdirSync, writeFileSync, readFileSync, unlinkSync } from "fs";
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
  next?: string;
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

interface Checkpoint {
  version: number;
  crawls: {
    [sourceName: string]: {
      crawlId: string;
      status: "started" | "polling" | "completed" | "failed";
      startedAt: string;
      completedAt?: string;
      pagesTotal?: number;
      pagesCompleted?: number;
      error?: string;
    };
  };
}

// ============================================================================
// Config & Checkpoint
// ============================================================================

const CHECKPOINT_VERSION = 1;

function loadConfig(): Config {
  const configPath = join(import.meta.dir, "..", "config.json");

  if (!existsSync(configPath)) {
    console.error("Error: config.json not found");
    console.error("Copy config.example.json to config.json and add your API keys");
    process.exit(1);
  }

  return JSON.parse(readFileSync(configPath, "utf-8"));
}

function getCheckpointPath(): string {
  return join(import.meta.dir, "..", "output", ".crawl-checkpoint.json");
}

function loadCheckpoint(): Checkpoint {
  const path = getCheckpointPath();

  if (existsSync(path)) {
    try {
      const data = JSON.parse(readFileSync(path, "utf-8"));
      if (data.version === CHECKPOINT_VERSION) {
        return data;
      }
    } catch {
      // Corrupted checkpoint, start fresh
    }
  }

  return { version: CHECKPOINT_VERSION, crawls: {} };
}

function saveCheckpoint(checkpoint: Checkpoint): void {
  const path = getCheckpointPath();
  const dir = join(import.meta.dir, "..", "output");

  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }

  writeFileSync(path, JSON.stringify(checkpoint, null, 2), "utf-8");
}

function clearCheckpoint(sourceName: string): void {
  const checkpoint = loadCheckpoint();
  delete checkpoint.crawls[sourceName];
  saveCheckpoint(checkpoint);
}

// ============================================================================
// Firecrawl API
// ============================================================================

const FIRECRAWL_API = "https://api.firecrawl.dev/v1";

async function startCrawl(
  apiKey: string,
  source: Source,
  checkpoint: Checkpoint
): Promise<string> {
  // Check if we have an existing crawl
  const existing = checkpoint.crawls[source.name];
  if (existing && existing.status === "polling") {
    console.log(`\nResuming crawl for: ${source.name}`);
    console.log(`  Crawl ID: ${existing.crawlId}`);
    return existing.crawlId;
  }

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

  // Save checkpoint
  checkpoint.crawls[source.name] = {
    crawlId: result.id,
    status: "polling",
    startedAt: new Date().toISOString(),
  };
  saveCheckpoint(checkpoint);

  return result.id;
}

async function pollCrawlStatus(
  apiKey: string,
  crawlId: string,
  sourceName: string,
  checkpoint: Checkpoint
): Promise<CrawlPage[]> {
  const maxAttempts = 3600; // 2 hours max (2s intervals)
  const pollInterval = 2000;
  const allPages: CrawlPage[] = [];

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

    // Update checkpoint with progress
    if (checkpoint.crawls[sourceName]) {
      checkpoint.crawls[sourceName].pagesTotal = result.total;
      checkpoint.crawls[sourceName].pagesCompleted = result.completed;
      saveCheckpoint(checkpoint);
    }

    if (result.status === "completed") {
      // Collect all pages (handle pagination)
      if (result.data) {
        allPages.push(...result.data);
      }

      // Check for more pages
      let nextUrl = result.next;
      while (nextUrl) {
        const nextResponse = await fetch(nextUrl, {
          headers: { Authorization: `Bearer ${apiKey}` },
        });
        const nextResult = (await nextResponse.json()) as CrawlResponse;
        if (nextResult.data) {
          allPages.push(...nextResult.data);
        }
        nextUrl = nextResult.next;
      }

      console.log(`\n  Crawl completed: ${allPages.length} pages total`);

      // Update checkpoint
      if (checkpoint.crawls[sourceName]) {
        checkpoint.crawls[sourceName].status = "completed";
        checkpoint.crawls[sourceName].completedAt = new Date().toISOString();
        saveCheckpoint(checkpoint);
      }

      return allPages;
    }

    if (result.status === "failed") {
      // Update checkpoint
      if (checkpoint.crawls[sourceName]) {
        checkpoint.crawls[sourceName].status = "failed";
        checkpoint.crawls[sourceName].error = result.error;
        saveCheckpoint(checkpoint);
      }
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
): number {
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
  return savedCount;
}

// ============================================================================
// Main
// ============================================================================

async function main() {
  console.log("=".repeat(60));
  console.log("GGU Documentation Crawler (with Checkpoint/Resume)");
  console.log("=".repeat(60));

  const config = loadConfig();
  const checkpoint = loadCheckpoint();

  // Parse command line args
  const args = process.argv.slice(2);
  const sourceFilter = args.includes("--source")
    ? args[args.indexOf("--source") + 1]
    : null;
  const resumeMode = args.includes("--resume");

  // Filter sources if specified
  const sources = sourceFilter
    ? config.sources.filter((s) => s.name === sourceFilter)
    : config.sources;

  if (sources.length === 0) {
    console.error(`No sources found${sourceFilter ? ` matching "${sourceFilter}"` : ""}`);
    process.exit(1);
  }

  console.log(`\nSources to crawl: ${sources.map((s) => s.name).join(", ")}`);

  // Show checkpoint status
  const existingCrawls = Object.entries(checkpoint.crawls)
    .filter(([name]) => sources.some((s) => s.name === name))
    .filter(([, c]) => c.status === "polling" || c.status === "completed");

  if (existingCrawls.length > 0) {
    console.log("\nCheckpoint status:");
    for (const [name, crawl] of existingCrawls) {
      console.log(`  - ${name}: ${crawl.status} (${crawl.pagesCompleted || 0}/${crawl.pagesTotal || "?"} pages)`);
    }
  }

  // Ensure output directory exists
  const outputDir = config.output.directory;
  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }

  // Crawl each source
  let totalPages = 0;

  for (const source of sources) {
    try {
      // Check if already completed
      const existing = checkpoint.crawls[source.name];
      if (existing?.status === "completed" && !resumeMode) {
        console.log(`\nSkipping ${source.name} (already completed)`);
        console.log(`  Use --clear-checkpoint to recrawl`);
        continue;
      }

      const crawlId = await startCrawl(config.firecrawl.apiKey, source, checkpoint);
      const pages = await pollCrawlStatus(config.firecrawl.apiKey, crawlId, source.name, checkpoint);
      const saved = savePages(pages, source.name, outputDir);
      totalPages += saved;

      // Clear checkpoint for this source (crawl complete)
      clearCheckpoint(source.name);
    } catch (error) {
      console.error(`\nError crawling ${source.name}:`, error);
      console.log("  You can resume with: bun run crawl --resume");
    }
  }

  console.log("\n" + "=".repeat(60));
  console.log("Crawl complete!");
  console.log(`Total pages saved: ${totalPages}`);
  console.log(`Output directory: ${outputDir}`);
  console.log("=".repeat(60));
}

main().catch(console.error);
