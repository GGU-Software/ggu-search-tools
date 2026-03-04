# Webinar-Indexer

Extrahiert strukturiertes Wissen aus GGU-Webinar-Aufzeichnungen.

## Ablauf

1. **Whisper** transkribiert Videos lokal (Modell: `medium`, Sprache: `de`, GPU wenn verfügbar)
2. **Fehlerkorrektur** via `corrections.tsv` — bekannte Whisper-Fehler automatisch beheben
3. **Claude** strukturiert jedes Transkript in ein Markdown-Dokument

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

## Batch-Verarbeitung

Videos in `videos/` ablegen, dann:

```bash
# Schritt 1: Alle Videos transkribieren (bereits transkribierte werden übersprungen)
python scripts/batch_transcribe.py

# Schritt 2: Alle Transkripte strukturieren (bereits strukturierte werden übersprungen)
python scripts/batch_structure.py
```

### Einzelnes Video (POC)

```bash
python scripts/run_poc.py videos/Berechnung\ und\ Bemessung\ von\ Verbauwänden.mp4
```

### Output

- `transcripts/raw/*.txt` — korrigiertes Whisper-Transkript
- `transcripts/structured/*.md` — Claude-strukturiertes Markdown

## Fehlerkorrektur (`corrections.tsv`)

Whisper produziert bei GGU-Fachbegriffen systematische Fehler. Die Datei `corrections.tsv` korrigiert diese automatisch:

```
# Format: falsch<TAB>richtig
Gigi Ubiten	GGU-Retain
Talsicherheitskonzept	Teilsicherheitskonzept
```

Neue Korrekturen einfach als Zeile ergänzen. Längere Patterns werden automatisch zuerst angewendet.

## GPU-Unterstützung

Whisper nutzt automatisch eine CUDA-fähige GPU wenn verfügbar. Device und fp16-Status werden beim Start geloggt. Ohne GPU: CPU-Fallback (langsamer, aber funktional).
