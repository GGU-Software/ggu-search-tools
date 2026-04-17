"""Download specific files from SharePoint by path and extract to markdown.

One-off script for norms the scanner missed (in Bibliothek/E/ subfolders).
"""
import asyncio
import sys
from pathlib import Path
from urllib.parse import quote

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.sharepoint.client import SharePointClient
from src.extraction.pdf_extractor import PDFExtractor

# Files to download: (norm_id, sharepoint_path_relative_to_drive_root)
FILES = [
    ("EAB", "Bibliothek/E/EAB/EAB 6.Auflage_2021.pdf"),
    ("EAU", "Bibliothek/E/EAU/EAU_2012_Auflage 11.pdf"),
    ("EBGEO", "Bibliothek/E/EBGEO/EBGEO_2010_2.Auflage.pdf"),
    ("EA-Pfaehle", "Bibliothek/E/EAP/EA-Pfahle, 2. Auflage 2012.pdf"),
    ("OENORM EN 1997-1", "Bibliothek/001_Normen/Ö-Norm/B 1997-1-1 Entwurf ÖNORM EC 7 Entwurf, Berechnung und Bemessung 2012_12.pdf"),
]

DOWNLOADS_DIR = Path(__file__).parent.parent / "downloads"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


async def download_by_path(client: SharePointClient, drive_path: str, save_as: Path) -> bool:
    """Download a file from SharePoint by its drive-relative path."""
    await client.ensure_valid_token()

    # Graph API: /drives/{drive-id}/root:/{path}:/content
    encoded_path = quote(drive_path, safe="/")
    url = f"{client.GRAPH_API_BASE}/drives/{client.drive_id}/root:/{encoded_path}:/content"

    session = await client.get_session()
    headers = client.get_auth_headers()

    async with session.get(url, headers=headers) as response:
        if response.status != 200:
            error_text = await response.text()
            print(f"  FAILED: {response.status} - {error_text[:200]}")
            return False

        content = await response.read()
        save_as.write_bytes(content)
        print(f"  OK ({len(content) // 1024} KB)")
        return True


async def main():
    print("=" * 60)
    print("MANUAL DOWNLOAD + EXTRACT")
    print("=" * 60)

    client = SharePointClient()
    if not await client.initialize():
        print("Failed to connect to SharePoint")
        return

    print(f"\nConnected. Downloading {len(FILES)} files...\n")

    downloaded = []
    for norm_id, sp_path in FILES:
        filename = sp_path.rsplit("/", 1)[-1]
        save_path = DOWNLOADS_DIR / filename
        print(f"[{norm_id}] {filename}...", end=" ", flush=True)

        if await download_by_path(client, sp_path, save_path):
            downloaded.append((norm_id, save_path))

    await client.close()

    if not downloaded:
        print("\nNo files downloaded.")
        return

    print(f"\n\nExtracting {len(downloaded)} PDFs to markdown...\n")
    extractor = PDFExtractor(enable_ocr=True)

    for norm_id, pdf_path in downloaded:
        out_name = pdf_path.stem + ".md"
        out_path = OUTPUT_DIR / out_name
        print(f"[{norm_id}] {pdf_path.name}...", end=" ", flush=True)

        try:
            markdown = extractor.extract_markdown(pdf_path)
            out_path.write_text(markdown, encoding="utf-8")
            words = len(markdown.split())
            print(f"OK ({words:,} words)")
        except Exception as e:
            print(f"FAILED: {e}")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
