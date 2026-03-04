# GGU-STABILITY & GGU-2D SS-Flow — Webinar-Zusammenfassung

## Zusammenfassung
Das Webinar zeigt das Zusammenspiel von untergrundhydraulischer Berechnung (GGU-2D SS-Flow) und Böschungsbruchuntersuchung (GGU-Stability) am Beispiel eines wasserbelasteten Deiches. Statt einer vereinfachten Sickerlinie werden Porenwasserdrücke physikalisch korrekt mit der Finite-Element-Methode berechnet und direkt in die erdstatische Berechnung übernommen. Verschiedene Sanierungsmaßnahmen (Fußfilter, Entspannungsbohrungen) werden als Varianten untersucht. Abschließend wird die Möglichkeit instationärer Berechnungen (zeitabhängiger Hochwasseranstieg) demonstriert.

## Dialog-Navigation

### GGU-2D SS-Flow (Untergrundhydraulik)
- `Knoten setzen` — Finite-Element-Knoten an maßgebenden Stellen platzieren
- `Elemente erzeugen` — FE-Netz aus Knoten generieren (automatisch oder manuell)
- `Elemente löschen` — Überflüssige Elemente entfernen
- `Bodenkennwerte` — Durchlässigkeiten je Bodennummer zuweisen (z.B. 10⁻⁷)
- `Potentialrandbedingungen` — Einstau-Wasserstand und Landseiten-Potential definieren
- `Netz verdichten` — Elementanzahl erhöhen für numerische Genauigkeit
- `Netz verbessern` — Topologie optimieren (gleichseitigere Dreiecke)
- `Berechnen` — Stationäre oder instationäre Strömungsberechnung
- `Isolinien` — Potentiallinienfeld und Porenwasserdruckverteilung darstellen
- `Datei > Exportieren in GGU-Stability` — Porenwasserdrucknetz für Erdstatik exportieren
- `Rohrelemente` — Linienartige Elemente für Entspannungsbohrungen/-öffnungen

### GGU-Stability (Erdstatik)
- `Geländeoberfläche definieren` — Per Mausklick aus untergrundhydraulischem Modell abfahren
- `Schichten einfügen` — Bodenschichtung mit erdstatischen Kennwerten (φ, c, γ)
- `Gleitkreise definieren` — Mittelpunkte und Radien für Versagensmechanismen festlegen
- `Porenwasserdrucknetz laden` — Exportierte hydraulische Einwirkungen importieren
- `Berechnen` — Standsicherheitsberechnung für alle definierten Gleitkreise
- `Farbdarstellung` — Standsicherheiten farbig visualisieren

## Kernfunktionen
- **Kopplung Hydraulik/Erdstatik**: Porenwasserdrücke aus FE-Berechnung direkt in Böschungsbruchuntersuchung übernehmen — keine vereinfachte Sickerlinie nötig
- **Geometrieübernahme**: Untergrundhydraulisches FE-Modell als Grundlage für erdstatisches Schichtmodell verwenden
- **Varianten schnell untersuchen**: Hydraulische Maßnahmen (Filter, Entspannung) modifizieren und sofort erdstatisch bewerten
- **Instationäre Berechnung**: Zeitabhängiger Hochwasseranstieg modellieren, beliebigen Zeitpunkt für Erdstatik herausgreifen
- **Physikalisch korrekte Porenwasserdrücke**: Geschichtete, inhomogene und anisotrope Untergrundverhältnisse berücksichtigt
- **Rohrelemente**: Entspannungsbohrungen als linienartige Elemente mit eigener Durchlässigkeit modellierbar

## Typische Workflows

### Workflow 1: Deich-Standsicherheit mit Grundwasserströmung berechnen

1. **GGU-2D SS-Flow**: Knoten an maßgebenden Stellen setzen, FE-Netz erzeugen
2. Bodenschichten zuweisen (Deichkörper, Deckschicht, Untergrund) mit Durchlässigkeiten
3. Potentialrandbedingungen definieren (Einstau-Wasserstand, Landseitenpotential)
4. Netz verdichten und Topologie verbessern
5. Stationäre Berechnung durchführen
6. Ergebnis (Porenwasserdrucknetz) exportieren für GGU-Stability
7. **GGU-Stability**: Grobes FE-Netz als Geometriegrundlage importieren
8. Geländeoberfläche und Schichtgrenzen per Maus abfahren
9. Erdstatische Bodenkennwerte zuweisen (φ, c, γ)
10. Gleitkreise (Mittelpunkte, Radien) definieren
11. Porenwasserdrucknetz aus Flow2D laden
12. Berechnen — maßgebenden Gleitkreis und Standsicherheit auswerten

### Workflow 2: Sanierungsmaßnahmen als Varianten untersuchen

1. Ausgangssystem wie Workflow 1 berechnen
2. **Variante A — Fußfilter**: In Flow2D Durchlässigkeit im Fußbereich erhöhen (z.B. 10⁻⁴), neu berechnen, exportieren, in Stability laden und Standsicherheit prüfen
3. **Variante B — Entspannungsbohrungen**: In Flow2D Rohrelemente einbauen (z.B. 20 cm, k=10⁻³), neu berechnen, exportieren, in Stability laden
4. Ergebnisse der Varianten vergleichen

### Workflow 3: Instationäre Betrachtung (Hochwasserwelle)

1. In Flow2D instationäre Berechnung mit zeitabhängigem Wasserstand durchführen
2. Beliebigen Zeitpunkt herausgreifen (z.B. Einstau nach 2 Tagen)
3. Zustand für diesen Zeitpunkt in Stability exportieren
4. Erdstatische Berechnung für gewählten Zeitpunkt durchführen

## Fachbegriffe

| Begriff | Erklärung |
|---------|-----------|
| Sickerlinie | Vereinfachte Darstellung der freien Wasseroberfläche im Erdbauwerk — nur für homogene Verhältnisse korrekt |
| Porenwasserdrucknetz | Aus FE-Berechnung exportiertes Feld der Porenwasserdrücke für jeden Punkt im System |
| Potentialrandbedingung | Vorgegebener Wasserstand an Systemrändern als Eingabe für die Strömungsberechnung |
| Super-Element-Netz | Grobes FE-Netz zur Geometriebeschreibung, wird vor Berechnung verdichtet |
| Gleitkreis | Kreisförmiger Versagensmechanismus für Böschungsbruchuntersuchung |
| Globalsicherheitskonzept | Standsicherheitsnachweis mit einem einzigen Sicherheitsfaktor (η) |
| Fußfilter/Fußdränage | Bereich erhöhter Durchlässigkeit am Böschungsfuß zur Reduzierung des Wasserdrucks |
| Entspannungsbohrungen | Gezielte Öffnungen zur Reduzierung von Porenwasserüberdruck im geschichteten System |
| Instationäre Berechnung | Zeitabhängige hydraulische Berechnung (z.B. Aufstau/Abstau einer Hochwasserwelle) |
| Rohrelemente | Linienartige FE-Elemente zur Modellierung von Dränagen, Filtern oder Entspannungsöffnungen |

## Häufige Fragen

- **Warum reicht eine einfache Sickerlinie nicht?**
  Bei geschichteten oder inhomogenen Baugrundverhältnissen (z.B. durchlässiger Deichuntergrund unter weniger durchlässigem Deichkörper) beschreibt eine einfache Sickerlinie die tatsächliche Porenwasserdruckverteilung nicht korrekt.

- **Wie überträgt man die hydraulischen Ergebnisse in die Erdstatik?**
  In Flow2D über `Datei > Exportieren in GGU-Stability` abspeichern, dann in Stability über `Porenwasserdrucknetz laden` importieren.

## Quelle
- **Titel**: Standsicherheiten von Gelände und Böschung — Einfluss von Grundwasserströmungen
- **Referent**: [unklar]
- **Software**: GGU-2D SS-Flow, GGU-Stability
