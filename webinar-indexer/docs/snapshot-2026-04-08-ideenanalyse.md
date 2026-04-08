# Webinar-Wissensextraktion: Analyse und Potential

> Snapshot vom 2026-04-08 — Dieses Dokument beschreibt den Stand zu diesem Zeitpunkt und wird nicht gepflegt.

## Ausgangslage (DEV-3101)

Die GGU-Entwicklung hat ein strukturelles Wissensproblem: Fachwissen über Programmabläufe, Workflows und Dialoge liegt bei den Fachkollegen, die kaum Zeit für Rückfragen haben. Die Dokumentation in den Repos ist lückenhaft, der Legacy-Code schwer lesbar. Das bremst sowohl manuelle Entwicklung als auch AI-gestützte Automatisierung — Claude Code fehlt Kontext zu Workflows, Dialognavigation und fachlichen Zusammenhängen.

GGU-Webinare (ca. 10-50 Aufzeichnungen) enthalten genau dieses fehlende Fachwissen. Experten erklären darin Programmfunktionen, Workflows und Dialoge.

## Was umgesetzt wurde

### 1. Transkriptions-Pipeline (DEV-3144)

Dreistufige Pipeline in `webinar-indexer/`:

```
MP4 Video → Whisper (GPU/CPU) → Fehlerkorrektur → Claude-Strukturierung → Markdown
```

- **Whisper-Transkription** mit automatischer GPU-Erkennung und CPU-Fallback
- **34 domänenspezifische Korrekturen** via `corrections.tsv` (z.B. "Gigi Ubiten" → "GGU-Retain", "Talsicherheitskonzept" → "Teilsicherheitskonzept")
- **Claude-Strukturierung** (Sonnet 4.6) mit standardisiertem Prompt: erzeugt Zusammenfassung, Dialog-Navigation, Kernfunktionen, Fachbegriffe, FAQ
- **Batch-fähig**: `batch_transcribe.py` und `batch_structure.py` verarbeiten alle Videos, überspringen bereits vorhandene

### 2. Verarbeitete Webinare

6 Webinare vollständig verarbeitet (Stand 2026-03-04):

| Webinar | App | Rohtranskript (Wörter) | Strukturiert (Zeilen / Wörter) |
|---------|-----|------------------------|-------------------------------|
| Bauphasen in GGU-Retain | RETAIN | 6.684 | 98 / 963 |
| Berechnung und Bemessung von Verbauwänden | RETAIN | 4.393 | 131 / 1.565 |
| Injektionssohlen mit GGU-Retain | RETAIN | 2.318 | 102 / 934 |
| Einstieg in GGU-SLAB | SLAB | 5.853 | 115 / 942 |
| GGU-STABILITY | STABILITY | 3.303 | 94 / 686 |
| Konsolidierungsschichten in GGU-STABILITY | STABILITY | 6.943 | 100 / 997 |

Gesamt: ~29.500 Wörter Rohtranskript, ~6.100 Wörter strukturierte Markdowns.

### 3. Knowledge-Skills für Claude Code (DEV-3145)

Drei app-spezifische Skills in `infra/ggu-dev-tools/claude-code/skills/`:

| Skill | Quellen | Umfang | Kernthemen |
|-------|---------|--------|------------|
| `@ggu-retain-knowledge` | 3 Webinare konsolidiert | 277 Zeilen / 18K | Verbauwand, Erddruck, Bauphasen, HDI, Teilsicherheit |
| `@ggu-slab-knowledge` | 1 Webinar | 115 Zeilen / 7.5K | Bettungsmodul, Steifemodulverfahren, FE-Netz, Priebe |
| `@ggu-stability-knowledge` | 2 Webinare | 183 Zeilen / 13K | Gleitkreis, Konsolidierung, Porenwasserdruck, GGU-2D SS-Flow |

Die Skills laden automatisch, wenn ein Entwickler im jeweiligen App-Repo arbeitet und liefern Kontext zu Berechnungsworkflows, Menüpfaden und Fachbegriffen.

### 4. Handbuch-Gap-Analyse (DEV-3146)

Systematischer Cross-Reference: Webinar-Wissen vs. Online-Handbuch (via ggu-public-docs MCP Server mit 25.000+ Seiten). Ergebnis:

| App | Gaps gesamt | FEHLT | UNVOLLSTÄNDIG | VERBESSERBAR |
|-----|-------------|-------|----------------|--------------|
| RETAIN | 16 | 7 | 5 | 4 |
| SLAB | 12 | 2 | 4 | 4 |
| STABILITY | 18 | 6 | 6 | 6 |
| **Summe** | **46** | **15** | **15** | **14** |

Gap Reports liegen in den jeweiligen App-Repos unter `docs/usermanual-updates/`.

## Ticket-Übersicht

```
DEV-3101  Done     Idee: Wissen aus Webinaren extrahieren
├── DEV-3144  Done     Batch-Transkription der Webinare
├── DEV-3145  Done     App-spezifische Knowledge-Skills
├── DEV-3146  Done     Webinar-Wissen ins Benutzerhandbuch
│   ├── DEV-3250  Backlog  RETAIN: 16 Handbuch-Gaps umsetzen
│   ├── DEV-3251  Backlog  SLAB: 12 Handbuch-Gaps umsetzen
│   └── DEV-3252  Backlog  STABILITY: 18 Handbuch-Gaps umsetzen
└── DEV-3502  Backlog  Autopilot-Skills mit Dialog-Navigation anreichern
```

## Ungenutztes Potential

### Mehr Webinare verarbeiten

Bisher 6 von geschätzt 10-50 Webinaren verarbeitet, nur 3 Apps abgedeckt. Weitere Webinare würden Knowledge-Skills für CONNECT, FOOTING, CANTILEVER, STRATIG etc. ermöglichen. Die Pipeline steht — der Aufwand pro Webinar ist minimal (Video in `videos/` legen, Batch-Skripte ausführen, Ergebnis prüfen).

**Einschränkung**: Die bisherigen Webinare sind älteren Datums — das extrahierte Wissen kann teilweise veraltet sein (geänderte Dialoge, neue Funktionen, aktualisierte Normen). Die Pipeline eignet sich aber genauso für neu aufgezeichnete Schulungen. Gezielt neue Schulungen aufzuzeichnen und zu verarbeiten wäre ein Weg, aktuelles Fachwissen systematisch zu erfassen.

### Autopilot-Skills mit Dialog-Navigation füttern (DEV-3502)

Die Skills `/autopilot-sd`, `/analyse-sd` und `/reproduce-behaviour` könnten Dialog-Navigationsdaten aus den Knowledge-Skills nutzen. Besonders `/reproduce-behaviour` (AutoIt-basierte GUI-Automatisierung) profitiert von konkreten Menüpfaden und Dialogstrukturen.

### 46 Handbuch-Gaps umsetzen (DEV-3250/3251/3252)

Die Gap-Analyse hat 46 konkrete Verbesserungsvorschläge für das Online-Handbuch identifiziert — 15 davon betreffen komplett fehlende Inhalte (z.B. Step-by-Step-Workflows für Bauphasen, Deich-Standsicherheit, Bettungsmodulverfahren). Das Material aus den Webinaren liefert die Vorlage.

### Support-FAQs

Die strukturierten Markdowns enthalten bereits FAQ-Abschnitte. Diese könnten als Grundlage für Support-Dokumentation dienen.

### Pinecone-Integration

Strukturierte Webinar-Dokumente könnten in den `ggu-public-docs` Pinecone-Index hochgeladen werden, um die MCP-Server-Antworten mit Workflow-Wissen anzureichern.

## Tech-Stack

- **Transkription**: OpenAI Whisper — AI-basierte Spracherkennung (medium model, Deutsch, GPU-beschleunigt)
- **Strukturierung**: Claude API (Sonnet 4.6, 8K-Token-Budget)
- **Fehlerkorrektur**: 34 domänenspezifische Korrekturregeln für Whisper-Erkennungsfehler
- **Skills**: Claude Code Markdown-basiertes Skill-System
- **Suche**: Pinecone MCP Assistants (ggu-public-docs, ggu-techdoc-search)
