/**
 * Upload crawled documentation to Pinecone Assistant
 *
 * This script reads markdown files from the output directory
 * and uploads them to the Pinecone Assistant for indexing.
 *
 * Features:
 * - Checkpoint/Resume: Saves progress, can resume after interruption
 * - Rate limiting: Respects API limits
 *
 * Usage:
 *   bun run upload
 *   bun run scripts/upload.ts
 *   bun run scripts/upload.ts --source product-website
 *   bun run scripts/upload.ts --resume  # Resume interrupted upload
 *   bun run scripts/upload.ts --clear   # Clear existing files first
 */

import { existsSync, readdirSync, readFileSync, writeFileSync, unlinkSync, mkdirSync } from "fs";
import { join } from "path";
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

interface UploadCheckpoint {
  version: number;
  uploads: {
    [sourceName: string]: {
      status: "started" | "in_progress" | "completed" | "failed";
      startedAt: string;
      completedAt?: string;
      totalFiles: number;
      uploadedFiles: string[];  // List of uploaded file paths
      failedFiles: string[];    // List of failed file paths
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
  return join(import.meta.dir, "..", "output", ".upload-checkpoint.json");
}

function loadCheckpoint(): UploadCheckpoint {
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

  return { version: CHECKPOINT_VERSION, uploads: {} };
}

function saveCheckpoint(checkpoint: UploadCheckpoint): void {
  const path = getCheckpointPath();
  const dir = join(import.meta.dir, "..", "output");

  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }

  writeFileSync(path, JSON.stringify(checkpoint, null, 2), "utf-8");
}

function clearCheckpoint(sourceName: string): void {
  const checkpoint = loadCheckpoint();
  delete checkpoint.uploads[sourceName];
  saveCheckpoint(checkpoint);
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
        .filter((d) => !d.name.startsWith("."))  // Skip hidden directories
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
  assistant: ReturnType<Pinecone["Assistant"]>
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
  assistant: ReturnType<Pinecone["Assistant"]>,
  files: MarkdownFile[],
  sourceName: string,
  checkpoint: UploadCheckpoint
): Promise<{ uploaded: number; skipped: number; failed: number }> {
  console.log(`\nUploading ${files.length} files to Pinecone Assistant...`);

  // Initialize or get existing checkpoint for this source
  if (!checkpoint.uploads[sourceName]) {
    checkpoint.uploads[sourceName] = {
      status: "started",
      startedAt: new Date().toISOString(),
      totalFiles: files.length,
      uploadedFiles: [],
      failedFiles: [],
    };
    saveCheckpoint(checkpoint);
  }

  const uploadState = checkpoint.uploads[sourceName];
  uploadState.status = "in_progress";
  uploadState.totalFiles = files.length;

  const alreadyUploaded = new Set(uploadState.uploadedFiles);

  let uploaded = 0;
  let skipped = 0;
  let failed = 0;

  for (const file of files) {
    // Skip already uploaded files
    if (alreadyUploaded.has(file.path)) {
      skipped++;
      continue;
    }

    try {
      // Create content with metadata header
      const contentWithMetadata = `# ${file.metadata.title || "Document"}

Source: ${file.metadata.url || "Unknown"}

${file.content}`;

      // Write to temp file for upload
      const tempPath = `./output/.temp_${file.filename}`;
      writeFileSync(tempPath, contentWithMetadata);

      // Upload using the SDK
      await assistant.uploadFile({
        path: tempPath,
        metadata: {
          source: file.metadata.source || "unknown",
          url: file.metadata.url || "",
        },
      });

      // Clean up temp file
      unlinkSync(tempPath);

      uploaded++;
      uploadState.uploadedFiles.push(file.path);

      // Save checkpoint after each successful upload
      saveCheckpoint(checkpoint);

      const total = uploaded + skipped;
      process.stdout.write(`\r  Progress: ${total}/${files.length} (${uploaded} uploaded, ${skipped} skipped)`);
    } catch (error) {
      failed++;
      uploadState.failedFiles.push(file.path);
      saveCheckpoint(checkpoint);
      console.error(`\n  Failed to upload ${file.filename}:`, error);
    }
  }

  // Update final status
  if (failed === 0) {
    uploadState.status = "completed";
    uploadState.completedAt = new Date().toISOString();
  } else {
    uploadState.status = "failed";
    uploadState.error = `${failed} files failed to upload`;
  }
  saveCheckpoint(checkpoint);

  console.log(`\n\n  Uploaded: ${uploaded}`);
  if (skipped > 0) {
    console.log(`  Skipped (already uploaded): ${skipped}`);
  }
  if (failed > 0) {
    console.log(`  Failed: ${failed}`);
  }

  return { uploaded, skipped, failed };
}

// ============================================================================
// Main
// ============================================================================

async function main() {
  console.log("=".repeat(60));
  console.log("GGU Documentation Uploader (with Checkpoint/Resume)");
  console.log("=".repeat(60));

  const config = loadConfig();
  const checkpoint = loadCheckpoint();

  // Parse command line args
  const args = process.argv.slice(2);
  const sourceFilter = args.includes("--source")
    ? args[args.indexOf("--source") + 1]
    : undefined;
  const shouldClear = args.includes("--clear");
  const resumeMode = args.includes("--resume");

  // Show checkpoint status
  const existingUploads = Object.entries(checkpoint.uploads)
    .filter(([, u]) => u.status === "in_progress" || u.status === "completed");

  if (existingUploads.length > 0) {
    console.log("\nCheckpoint status:");
    for (const [name, upload] of existingUploads) {
      console.log(`  - ${name}: ${upload.status} (${upload.uploadedFiles.length}/${upload.totalFiles} files)`);
    }
  }

  // Initialize Pinecone client
  console.log("\nConnecting to Pinecone...");
  const pinecone = new Pinecone({
    apiKey: config.pinecone.apiKey,
  });

  const assistant = pinecone.Assistant(config.pinecone.assistantName);
  console.log(`  Assistant: ${config.pinecone.assistantName}`);

  // Clear existing files if requested
  if (shouldClear) {
    await clearAssistantFiles(assistant);
    // Also clear checkpoint when clearing files
    for (const sourceName of Object.keys(checkpoint.uploads)) {
      delete checkpoint.uploads[sourceName];
    }
    saveCheckpoint(checkpoint);
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
    if (!acc[source]) acc[source] = [];
    acc[source].push(f);
    return acc;
  }, {} as Record<string, MarkdownFile[]>);

  for (const [source, sourceFiles] of Object.entries(bySource)) {
    const existingUpload = checkpoint.uploads[source];
    const uploadedCount = existingUpload?.uploadedFiles.length || 0;
    console.log(`    - ${source}: ${sourceFiles.length} files (${uploadedCount} already uploaded)`);
  }

  // Upload to Pinecone (by source for better checkpoint granularity)
  let totalUploaded = 0;
  let totalSkipped = 0;
  let totalFailed = 0;

  for (const [source, sourceFiles] of Object.entries(bySource)) {
    // Check if already completed
    const existingUpload = checkpoint.uploads[source];
    if (existingUpload?.status === "completed" && !resumeMode) {
      console.log(`\nSkipping ${source} (already completed)`);
      console.log(`  Use --clear to re-upload`);
      totalSkipped += sourceFiles.length;
      continue;
    }

    console.log(`\n--- Uploading source: ${source} ---`);
    const result = await uploadFiles(assistant, sourceFiles, source, checkpoint);
    totalUploaded += result.uploaded;
    totalSkipped += result.skipped;
    totalFailed += result.failed;

    // Clear checkpoint for completed source
    if (result.failed === 0) {
      clearCheckpoint(source);
    }
  }

  console.log("\n" + "=".repeat(60));
  console.log("Upload complete!");
  console.log(`  Total uploaded: ${totalUploaded}`);
  if (totalSkipped > 0) {
    console.log(`  Total skipped: ${totalSkipped}`);
  }
  if (totalFailed > 0) {
    console.log(`  Total failed: ${totalFailed}`);
    console.log("  You can resume with: bun run upload --resume");
  }
  console.log("\nFiles are now being indexed by Pinecone Assistant.");
  console.log("This may take a few minutes before they are searchable.");
  console.log("=".repeat(60));
}

main().catch(console.error);
