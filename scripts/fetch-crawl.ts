/**
 * Fetch crawl results directly from Firecrawl API
 */
import { mkdirSync, writeFileSync, existsSync } from "fs";

const crawlId = process.argv[2] || "019bc0a7-cc94-75af-a3f9-5df5f1fcf5bc";
const apiKey = "fc-6ae998fe019149e0aba7e39096183da0";

async function fetchAllData() {
  const outputDir = "./output/product-website";
  if (!existsSync(outputDir)) {
    mkdirSync(outputDir, { recursive: true });
  }

  console.log(`Fetching crawl ${crawlId}...`);

  const response = await fetch(`https://api.firecrawl.dev/v1/crawl/${crawlId}`, {
    headers: { Authorization: `Bearer ${apiKey}` },
  });
  const result = (await response.json()) as {
    status: string;
    completed: number;
    total: number;
    data?: Array<{
      markdown?: string;
      metadata?: {
        title?: string;
        sourceURL?: string;
      };
    }>;
  };

  console.log(`Status: ${result.status}`);
  console.log(`Pages: ${result.completed}/${result.total}`);
  console.log(`Data items: ${result.data?.length || 0}`);

  if (!result.data) {
    console.log("No data available yet");
    return;
  }

  let saved = 0;
  for (const page of result.data) {
    if (!page.markdown || !page.metadata?.sourceURL) continue;

    const filename =
      page.metadata.sourceURL
        .replace(/^https?:\/\//, "")
        .replace(/[^a-zA-Z0-9-_.]/g, "_")
        .substring(0, 200) + ".md";

    const content = `---
title: ${JSON.stringify(page.metadata.title || "Untitled")}
url: ${JSON.stringify(page.metadata.sourceURL)}
---

${page.markdown}`;

    writeFileSync(`${outputDir}/${filename}`, content);
    saved++;
  }
  console.log(`Saved ${saved} files to ${outputDir}`);
}

fetchAllData().catch(console.error);
