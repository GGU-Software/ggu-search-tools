/**
 * Upload crawled documentation to Pinecone Assistant via REST API
 * (Avoids SDK issues with Bun)
 */

import { appendFileSync, existsSync, readdirSync, readFileSync, createReadStream } from "fs";
import { join } from "path";

// ============================================================================
// Types
// ============================================================================

interface Config {
  pinecone: {
    apiKey: string;
    assistantName: string;
    // Regions-Host des Assistenten. EU: https://prod-eu-data.ke.pinecone.io
    // Ablesen unter GET /assistant/assistants/<name>, Feld "host" -- nicht raten.
    host?: string;
  };
  output: {
    directory: string;
  };
}

interface MarkdownFile {
  path: string;
  filename: string;
  content: string;
  metadata: {
    title?: string;
    url?: string;
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

  for (const line of frontmatter.split("\n")) {
    const colonIndex = line.indexOf(":");
    if (colonIndex > 0) {
      const key = line.substring(0, colonIndex).trim();
      let value = line.substring(colonIndex + 1).trim();
      if ((value.startsWith('"') && value.endsWith('"')) ||
          (value.startsWith("'") && value.endsWith("'"))) {
        try {
          value = JSON.parse(value);
        } catch {}
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
        .filter((d) => d.isDirectory() && !d.name.startsWith("."))
        .map((d) => d.name);

  for (const sourceDir of sourceDirs) {
    const sourcePath = join(outputDir, sourceDir);

    if (!existsSync(sourcePath)) continue;

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
          source: sourceDir,
        },
      });
    }
  }

  return files;
}

// ============================================================================
// Pinecone REST API
// ============================================================================

const DEFAULT_ASSISTANT_API = "https://prod-1-data.ke.pinecone.io";

// Delay helper for rate limiting
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Namen der Dateien, die im Assistenten schon liegen.
 *
 * Ohne diese Abfrage legt jeder Wiederholungslauf Dubletten an: die API laedt eine Datei
 * mit gleichem Namen einfach ein zweites Mal hoch. Bei knapp 10.000 Dateien und Stunden
 * Laufzeit ist ein Abbruch der Normalfall -- und die Folge ist messbar. Im alten Index
 * belegte dieselbe Datei zwei von acht Treffern.
 */
/**
 * Lokaler Checkpoint: Namen aller Dateien, die dieser Rechner schon erfolgreich
 * geladen hat. Zweite Quelle neben der Assistant-Dateiliste — s. Kopf dieser Datei.
 */
function loadCheckpoint(path: string): Set<string> {
  if (!existsSync(path)) return new Set<string>();
  return new Set(
    readFileSync(path, "utf-8")
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean)
  );
}

async function listExistingFiles(
  api: string,
  apiKey: string,
  assistantName: string
): Promise<Set<string>> {
  const names = new Set<string>();
  const response = await fetch(`${api}/assistant/files/${assistantName}`, {
    headers: { "Api-Key": apiKey },
  });
  if (!response.ok) {
    console.error(
      `  Warnung: Dateiliste nicht abrufbar (${response.status}) -- es wird nichts uebersprungen`
    );
    return names;
  }
  const data = (await response.json()) as { files?: Array<{ name?: string }> };
  for (const f of data.files ?? []) {
    if (f.name) names.add(f.name);
  }
  return names;
}

async function uploadFile(
  api: string,
  apiKey: string,
  assistantName: string,
  file: MarkdownFile,
  retries: number = 3
): Promise<boolean> {
  // Prepare content with metadata header
  const content = `# ${file.metadata.title || "Document"}

Source URL: ${file.metadata.url || "Unknown"}

${file.content}`;

  // Create form data
  const formData = new FormData();
  const blob = new Blob([content], { type: "text/markdown" });
  formData.append("file", blob, file.filename);

  for (let attempt = 1; attempt <= retries; attempt++) {
    try {
      const response = await fetch(
        `${api}/assistant/files/${assistantName}`,
        {
          method: "POST",
          headers: {
            "Api-Key": apiKey,
          },
          body: formData,
        }
      );

      if (response.ok) {
        return true;
      }

      // Handle rate limiting with exponential backoff
      if (response.status === 429) {
        const retryAfter = response.headers.get("Retry-After");
        const waitTime = retryAfter ? parseInt(retryAfter) * 1000 : Math.pow(2, attempt) * 1000;
        if (attempt < retries) {
          console.error(`\n  Rate limited, waiting ${waitTime/1000}s before retry ${attempt + 1}...`);
          await delay(waitTime);
          continue;
        }
      }

      const error = await response.text();
      console.error(`\n  Error uploading ${file.filename}: ${response.status} - ${error}`);
      return false;
    } catch (error) {
      if (attempt < retries) {
        console.error(`\n  Network error, retrying...`);
        await delay(1000);
        continue;
      }
      console.error(`\n  Error uploading ${file.filename}:`, error);
      return false;
    }
  }
  return false;
}

// ============================================================================
// Main
// ============================================================================

async function main() {
  console.log("=".repeat(60));
  console.log("GGU Documentation Uploader (REST API)");
  console.log("=".repeat(60));

  const config = loadConfig();

  // Parse command line args
  const args = process.argv.slice(2);
  const sourceFilter = args.includes("--source")
    ? args[args.indexOf("--source") + 1]
    : undefined;

  const api = config.pinecone.host ?? DEFAULT_ASSISTANT_API;
  console.log(`\nAssistant: ${config.pinecone.assistantName}`);
  console.log(`Host:      ${api}`);

  // Load markdown files
  console.log("\nLoading markdown files...");
  const files = loadMarkdownFiles(config.output.directory, sourceFilter);

  if (files.length === 0) {
    console.error("No markdown files found");
    process.exit(1);
  }

  console.log(`  Found ${files.length} files`);

  // Bereits vorhandene Dateien ueberspringen -> der Lauf ist wiederholbar, ohne Dubletten.
  const existing = await listExistingFiles(
    api,
    config.pinecone.apiKey,
    config.pinecone.assistantName
  );
  const checkpointPath = join(config.output.directory, ".uploaded-" + config.pinecone.assistantName + ".log");
  const checkpoint = loadCheckpoint(checkpointPath);
  const pending = files.filter(
    (f) => !existing.has(f.filename) && !checkpoint.has(f.filename)
  );
  console.log(
    `  Bereits im Assistenten: ${existing.size}, im lokalen Checkpoint: ${checkpoint.size}`
  );
  console.log(
    `  -> ${files.length - pending.length} uebersprungen, ${pending.length} zu laden`
  );
  if (pending.length === 0) {
    console.log("\nNichts zu tun -- alle Dateien liegen bereits im Assistenten.");
    return;
  }

  // Upload to Pinecone
  console.log(`\nUploading to Pinecone Assistant...`);

  let uploaded = 0;
  let failed = 0;

  for (const file of pending) {
    const success = await uploadFile(
      api,
      config.pinecone.apiKey,
      config.pinecone.assistantName,
      file
    );

    if (success) {
      uploaded++;
      // Sofort protokollieren, nicht am Ende: bei einem Abbruch (oder wenn der Rechner
      // ausgeschaltet wird) ist genau das der Zustand, auf dem der naechste Lauf aufbaut.
      appendFileSync(checkpointPath, file.filename + "\n", "utf-8");
    } else {
      failed++;
    }

    process.stdout.write(`\r  Progress: ${uploaded + failed}/${pending.length} (${uploaded} ok, ${failed} failed)`);

    // Small delay between uploads to avoid rate limiting
    await delay(500);
  }

  console.log(`\n\n  Uploaded: ${uploaded}`);
  if (failed > 0) {
    console.log(`  Failed: ${failed}`);
  }

  console.log("\n" + "=".repeat(60));
  console.log("Upload complete!");
  console.log("Files may take a few minutes to be indexed and searchable.");
  console.log("=".repeat(60));
}

main().catch(console.error);
