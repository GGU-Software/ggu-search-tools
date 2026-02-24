# Webinar-Indexer (POC)

Extrahiert strukturiertes Wissen aus GGU-Webinar-Aufzeichnungen.

**Status**: POC — ein einzelnes Video, lokale Verarbeitung.

## Ablauf

1. **Whisper** transkribiert das Video lokal (Modell: `medium`, Sprache: `de`)
2. **Claude** strukturiert das Transkript in ein Markdown-Dokument

## Voraussetzungen

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) als System-Binary (`ffmpeg -version`)
- `ANTHROPIC_API_KEY` in `.env`

## Setup

```bash
cd infra/ggu-search-tools/webinar-indexer
cp .env.example .env        # API-Key eintragen
pip install -r requirements.txt
```

## Nutzung

```bash
python scripts/run_poc.py videos/Berechnung\ und\ Bemessung\ von\ Verbauwänden.mp4
```

Output:
- `transcripts/raw/*.txt` — Whisper-Rohtranskript
- `transcripts/structured/*.md` — Claude-strukturiertes Markdown

## Bewertungskriterien

- Transkriptqualität (Fachbegriffe korrekt?)
- Strukturierung (alle Sections sinnvoll gefüllt?)
- Menüpfade und Workflows erkennbar?
