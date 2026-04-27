"""A/B retrieval comparison between ggu-techdoc-search (md, US) and
ggu-techdoc-search-pdf (pdf, EU).

Hits both /context endpoints with the same query, collects top-K snippets,
and tabulates source / score / pages side-by-side.

Output:
  - Console summary
  - Markdown report at /tmp/ab-results.md
"""
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import quote
import urllib.request
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

API_KEY = os.environ["PINECONE_API_KEY"]
TOP_K = 5

ASSISTANTS = {
    "md": ("ggu-techdoc-search", "https://prod-1-data.ke.pinecone.io"),
    "pdf": ("ggu-techdoc-search-pdf", "https://prod-eu-data.ke.pinecone.io"),
}

# 10 questions covering: current DIN norms, DGGT books, scanned-only PDFs,
# multi-norm topics. Mix is intentional — some should be ties, some should
# expose the PDF-only multimodal advantage.
QUESTIONS = [
    ("DIN 1054 GZV", "Wie ist der Nachweis der Gebrauchstauglichkeit nach DIN 1054 zu führen?"),
    ("DIN EN 1997-1 BS", "Welche Bemessungssituationen kennt DIN EN 1997-1: BS-P, BS-T, BS-A und BS-E?"),
    ("DIN 4085 Erddruck", "Wie wird der passive Erddruckbeiwert nach DIN 4085 bestimmt?"),
    ("EAB Baugruben", "Was sagt EAB zu verankerten Baugrubenwänden und der Lastabtragung?"),
    ("EAU Auftriebssicherheit", "Welche Anforderungen stellt EAU an die Auftriebssicherheit von Kaimauern?"),
    ("EA-Pfähle (EAP)", "Wie bemisst EA-Pfähle axial belastete Pfähle?"),
    ("EBGEO Geokunststoffe", "Wie dimensioniert EBGEO bewehrte Stützkörper aus Geokunststoffen?"),
    ("DIN 4084 Standsicherheit", "Welche Eingangswerte braucht die Standsicherheitsberechnung nach DIN 4084?"),
    ("VDI 4640 Erdwärme", "Welche Bemessungsgrundsätze nennt VDI 4640 für Erdwärmesonden?"),
    ("DIN 18127 Proctor", "Wie wird der Proctor-Versuch nach DIN 18127 durchgeführt?"),
]


def query(target: str, q: str, top_k: int = TOP_K) -> dict:
    name, base = ASSISTANTS[target]
    url = f"{base}/assistant/chat/{name}/context"
    body = json.dumps({"messages": [{"role": "user", "content": q}], "top_k": top_k}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Api-Key": API_KEY, "Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return {"data": data, "ms": elapsed_ms}


def short_name(snippet: dict) -> str:
    ref = snippet.get("reference") or {}
    file = ref.get("file") or {}
    meta = file.get("metadata") or {}
    name = meta.get("filename") or file.get("name") or "?"
    # Trim
    name = name.replace(".pdf", "").replace(".md", "")
    if len(name) > 50:
        name = name[:47] + "…"
    return name


def pages_of(snippet: dict) -> str:
    ref = snippet.get("reference") or {}
    pages = ref.get("pages") or []
    if not pages:
        return "—"
    if len(pages) == 1:
        return f"S.{pages[0]}"
    return f"S.{pages[0]}-{pages[-1]}"


def render_block(label: str, q: str, result: dict) -> list[str]:
    lines = [f"### {label} _(in {result['ms']:.0f}ms)_", ""]
    snippets = result["data"].get("snippets", []) or []
    if not snippets:
        lines += ["_(no snippets)_", ""]
        return lines
    lines += ["| # | Score | Page | Source |", "|---|------:|------|--------|"]
    for i, s in enumerate(snippets, 1):
        score = s.get("score", 0.0)
        lines.append(f"| {i} | {score:.3f} | {pages_of(s)} | {short_name(s)} |")
    lines.append("")
    return lines


def overlap_pct(md: list, pdf: list) -> int:
    md_names = {short_name(s) for s in md}
    pdf_names = {short_name(s) for s in pdf}
    if not md_names and not pdf_names:
        return 0
    inter = md_names & pdf_names
    union = md_names | pdf_names
    return round(100 * len(inter) / len(union)) if union else 0


def md_unique(md: list, pdf: list) -> set[str]:
    return {short_name(s) for s in md} - {short_name(s) for s in pdf}


def pdf_unique(md: list, pdf: list) -> set[str]:
    return {short_name(s) for s in pdf} - {short_name(s) for s in md}


def main():
    print(f"A/B test — {len(QUESTIONS)} questions, top-{TOP_K} per assistant\n")
    report = ["# A/B Test: ggu-techdoc-search (md) vs ggu-techdoc-search-pdf (pdf)\n"]
    report.append(f"_{len(QUESTIONS)} questions, top-{TOP_K} snippets per assistant._\n")

    md_total_ms = 0.0
    pdf_total_ms = 0.0
    md_zero = 0
    pdf_zero = 0
    pdf_with_pages = 0
    overlaps = []
    rows = []

    for label, q in QUESTIONS:
        print(f"  {label}...", end=" ", flush=True)
        try:
            md_res = query("md", q)
            pdf_res = query("pdf", q)
        except Exception as e:
            print(f"FAIL: {e}")
            continue

        md_snips = md_res["data"].get("snippets", []) or []
        pdf_snips = pdf_res["data"].get("snippets", []) or []

        md_total_ms += md_res["ms"]
        pdf_total_ms += pdf_res["ms"]
        if not md_snips:
            md_zero += 1
        if not pdf_snips:
            pdf_zero += 1
        for s in pdf_snips:
            if (s.get("reference") or {}).get("pages"):
                pdf_with_pages += 1
                break

        ov = overlap_pct(md_snips, pdf_snips)
        overlaps.append(ov)

        rows.append((label, len(md_snips), len(pdf_snips), ov,
                     md_res["ms"], pdf_res["ms"],
                     ", ".join(sorted(md_unique(md_snips, pdf_snips)))[:60],
                     ", ".join(sorted(pdf_unique(md_snips, pdf_snips)))[:60]))

        # Detail block
        report.append(f"## {label}\n")
        report.append(f"**Q:** {q}\n")
        report.append(f"_Top-source overlap: {ov}%_\n")
        report.extend(render_block("md", q, md_res))
        report.extend(render_block("pdf", q, pdf_res))

        print(f"md={len(md_snips)} pdf={len(pdf_snips)} overlap={ov}%")

    # Summary
    n = len(QUESTIONS)
    avg_overlap = round(sum(overlaps) / max(1, len(overlaps)))
    summary = [
        "\n# Summary\n",
        f"| Metric | md | pdf |",
        f"|--------|----|-----|",
        f"| Avg latency (ms) | {md_total_ms / n:.0f} | {pdf_total_ms / n:.0f} |",
        f"| Questions returning 0 snippets | {md_zero} | {pdf_zero} |",
        f"| Questions where pdf returned ≥1 page | — | {pdf_with_pages} |",
        f"| Avg top-source overlap | {avg_overlap}% | |",
        "",
        "## Per-question breakdown\n",
        "| Question | md | pdf | overlap | md-only sources | pdf-only sources |",
        "|----------|---:|----:|--------:|-----------------|------------------|",
    ]
    for label, m, p, ov, mm, pm, mu, pu in rows:
        summary.append(f"| {label} | {m} | {p} | {ov}% | {mu} | {pu} |")

    report = summary + ["\n---\n"] + report

    Path("/tmp/ab-results.md").write_text("\n".join(report), encoding="utf-8")
    print(f"\nReport: /tmp/ab-results.md ({len(report)} lines)")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
