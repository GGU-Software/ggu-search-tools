/**
 * Upload crawled documentation to Pinecone Assistant
 *
 * This script reads markdown files from the output directory
 * and uploads them to the Pinecone Assistant for indexing.
 *
 * Usage:
 *   bun run upload
 *   bun run scripts/upload.ts
 *   bun run scripts/upload.ts --source product-website
 *   bun run scripts/upload.ts --clear  # Clear existing files first
 */

import { existsSync, readdirSync, readFileSync } from "fs";
import { join, basename } from "path";
import { Pinecone } from "@pinecone-database/pinecone";

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
}

interface MarkdownFile {
  path: string;
  filename: string;
  content: string;
  metadata: {
    title?: string;
    url?: string;
    description?: string;
    source?: string;
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
// File Reading
// ============================================================================

function parseFrontmatter(content: string): { metadata: Record<string, string>; body: string } {
  const frontmatterRegex = /^---\n([\s\S]*?)\n---\n([\s\S]*)$/;
  const match = content.match(frontmatterRegex);

  if (!match) {
    return { metadata: {}, body: content };
  }

  const metadata: Record<string, string> = {};
  const frontmatter = match[1];
  const body = match[2];

  // Parse YAML-like frontmatter
  for (const line of frontmatter.split("\n")) {
    const colonIndex = line.indexOf(":");
    if (colonIndex > 0) {
      const key = line.substring(0, colonIndex).trim();
      let value = line.substring(colonIndex + 1).trim();

      // Remove quotes
      if ((value.startsWith('"') && value.endsWith('"')) ||
          (value.startsWith("'") && value.endsWith("'"))) {
        value = JSON.parse(value);
      }

      metadata[key] = value;
    }
  }

  return { metadata, body };
}

function loadMarkdownFiles(outputDir: string, sourceName?: string): MarkdownFile[] {
  const files: MarkdownFile[] = [];

  const sourceDirs = sourceName
    ? [sourceName]
    : readdirSync(outputDir, { withFileTypes: true })
        .filter((d) => d.isDirectory())
        .map((d) => d.name);

  for (const sourceDir of sourceDirs) {
    const sourcePath = join(outputDir, sourceDir);

    if (!existsSync(sourcePath)) {
      console.warn(`Source directory not found: ${sourcePath}`);
      continue;
    }

    const mdFiles = readdirSync(sourcePath).filter((f) => f.endsWith(".md"));

    for (const mdFile of mdFiles) {
      const filepath = join(sourcePath, mdFile);
      const content = readFileSync(filepath, "utf-8");
      const { metadata, body } = parseFrontmatter(content);

      files.push({
        path: filepath,
        filename: mdFile,
        content: body,
        metadata: {
          title: metadata.title,
          url: metadata.url,
          description: metadata.description,
          source: sourceDir,
        },
      });
    }
  }

  return files;
}

// ============================================================================
// Pinecone Upload
// ============================================================================

async function clearAssistantFiles(
  assistant: ReturnType<Pinecone["assistant"]>
): Promise<void> {
  console.log("\nClearing existing files from assistant...");

  try {
    const existingFiles = await assistant.listFiles();

    if (existingFiles.files && existingFiles.files.length > 0) {
      console.log(`  Found ${existingFiles.files.length} existing files`);

      for (const file of existingFiles.files) {
        if (file.id) {
          await assistant.deleteFile(file.id);
          process.stdout.write(".");
        }
      }
      console.log("\n  Cleared all existing files");
    } else {
      console.log("  No existing files to clear");
    }
  } catch (error) {
    console.warn("  Could not clear files:", error);
  }
}

async function uploadFiles(
  assistant: ReturnType<Pinecone["assistant"]>,
  files: MarkdownFile[]
): Promise<void> {
  console.log(`\nUploading ${files.length} files to Pinecone Assistant...`);

  let uploaded = 0;
  let failed = 0;

  for (const file of files) {
    try {
      // Create a Blob from the content with metadata in the filename
      // Pinecone Assistant extracts metadata from the file content
      const contentWithMetadata = `# ${file.metadata.title || "Document"}

Source: ${file.metadata.url || "Unknown"}

${file.content}`;

      // Upload using the SDK
      // Note: The SDK expects a file path or File object
      // We'll create a temporary approach using the content directly
      const blob = new Blob([contentWithMetadata], { type: "text/markdown" });
      const fileObj = new File([blob], file.filename, { type: "text/markdown" });

      await assistant.uploadFile(fileObj);

      uploaded++;
      process.stdout.write(`\r  Progress: ${uploaded}/${files.length} uploaded`);
    } catch (error) {
      failed++;
      console.error(`\n  Failed to upload ${file.filename}:`, error);
    }
  }

  console.log(`\n\n  Uploaded: ${uploaded}`);
  if (failed > 0) {
    console.log(`  Failed: ${failed}`);
  }
}

// ============================================================================
// Main
// ============================================================================

async function main() {
  console.log("=".repeat(60));
  console.log("GGU Documentation Uploader");
  console.log("=".repeat(60));

  const config = loadConfig();

  // Parse command line args
  const args = process.argv.slice(2);
  const sourceFilter = args.includes("--source")
    ? args[args.indexOf("--source") + 1]
    : undefined;
  const shouldClear = args.includes("--clear");

  // Initialize Pinecone client
  console.log("\nConnecting to Pinecone...");
  const pinecone = new Pinecone({
    apiKey: config.pinecone.apiKey,
  });

  const assistant = pinecone.assistant(config.pinecone.assistantName);
  console.log(`  Assistant: ${config.pinecone.assistantName}`);

  // Clear existing files if requested
  if (shouldClear) {
    await clearAssistantFiles(assistant);
  }

  // Load markdown files
  console.log("\nLoading markdown files...");
  const files = loadMarkdownFiles(config.output.directory, sourceFilter);

  if (files.length === 0) {
    console.error("No markdown files found in output directory");
    console.error("Run 'bun run crawl' first to crawl the documentation");
    process.exit(1);
  }

  console.log(`  Found ${files.length} files`);

  // Group by source
  const bySource = files.reduce((acc, f) => {
    const source = f.metadata.source || "unknown";
    acc[source] = (acc[source] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  for (const [source, count] of Object.entries(bySource)) {
    console.log(`    - ${source}: ${count} files`);
  }

  // Upload to Pinecone
  await uploadFiles(assistant, files);

  console.log("\n" + "=".repeat(60));
  console.log("Upload complete!");
  console.log("Files are now being indexed by Pinecone Assistant.");
  console.log("This may take a few minutes before they are searchable.");
  console.log("=".repeat(60));
}

main().catch(console.error);
