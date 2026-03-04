# Konsolidierungsschichten in GGU-Stability — Webinar-Zusammenfassung

## Zusammenfassung
Das Webinar zeigt, wie Konsolidierungsprozesse bei Böschungsbruchuntersuchungen mit GGU-Stability berücksichtigt werden. Anhand eines Dammes auf bindigem Boden (Klei) wird demonstriert, wie Porenwasserüberdrücke durch spontane Belastung (Auffüllung, Verkehrslast) in Konsolidierungsschichten definiert und ihre zeitabhängige Dissipation in die Standsicherheitsberechnung einbezogen wird. Es werden mehrere Konsolidierungsschichten für verschiedene Lastanteile überlagert, verschiedene Konsolidierungszeitpunkte untersucht und als Problemlösung der Einsatz von Vertikaldrainagen zur Beschleunigung der Konsolidierung vorgeführt. Im Hintergrund berechnet das Programm die Isochronen analog zu GGU-Consolidate.

## Dialog-Navigation
- `Datei > Neu` — Neues System, EC7, Böschungsbruch, Lamellen, Porenwasserdrucklinie
- `Editor 1 > Eingeben > Geländepunkte` — Geländeoberkante tabellarisch bearbeiten
- `Editor 1 > Eingeben > Bodenschichten` — Anzahl und Geometrie der Bodenschichten definieren (Basislinie + Bodennummer)
- `Editor 1 > Eingeben > Konsolidierungsschichten` — Bis zu 30 Konsolidierungsschichten, Verlauf ändern, Bodenkennwerte (Es, kf), Entwässerungsbedingungen, Liegezeit
- `Editor 1 > Eingeben > Ständige und Verkehrslasten` — Oberflächenlasten definieren (Basislinie, Größe, Position)
- `Editor 2 > Gelände` — Geländeoberkante per Mausklick setzen
- `Editor 2 > Schicht wählen` — Bodenschicht per Maus definieren (Basislinie mit Bodennummer)
- `Editor 2 > Wasserstände` — Wasserstand links/rechts per Maus oder Tabelle (Shift + rechte Maustaste)
- `Editor 2 > Porenwasserdruck` — Porenwasserdrucklinie per Maus/Tabelle definieren
- `Editor 2 > Konsolidierungsschichten` — Konsolidierungsschicht per Maus definieren (Ordinaten, Schichtdicke, Porenwasserüberdruck)
- `Editor 2 > Lasten > Verkehrslast` — Veränderliche Einwirkung per Maus setzen
- `System > Mittelpunkte` — Suchbereich für Gleitkreismittelpunkte definieren
- `System > Berechnen` — Lamellenanzahl, Berechnung starten
- `Ausnutzungsgrade > Einstellung` — Porenwasserüberdruck darstellen und beschriften
- `Plattformat` — Plotränder anpassen für bessere Darstellung

## Kernfunktionen
- **Konsolidierungsschichten**: Bis zu 30 unabhängige Schichten definierbar, nicht an Bodenschichtgrenzen gebunden — auch innerhalb einer Bodenschicht oder schichtübergreifend
- **Porenwasserüberdrücke als Eingabe**: Konsolidierungsspannung (= Porenwasserüberdruck zum Zeitpunkt t=0) wird geometrisch über Ordinaten und Schichtdicke definiert
- **Zeitabhängige Berechnung**: Beliebiger Konsolidierungszeitpunkt wählbar — Programm berechnet Isochronen im Hintergrund (analog GGU-Consolidate)
- **Individuelle Liegezeiten**: Jede Konsolidierungsschicht kann eine eigene Liegezeit erhalten — wichtig für gestaffelte Bauabläufe
- **Globale vs. schichtspezifische Zeit**: Globaler Zeitfaktor gilt für alle Schichten; individuelle Zeit pro Schicht für unterschiedliche Belastungszeitpunkte
- **Entwässerungsbedingungen**: Oben/unten offen oder geschlossen — beeinflusst Konsolidierungsdauer und Isochronenverlauf
- **Vertikaldrainagen**: Drainageabstand und -radius je Konsolidierungsschicht definierbar — beschleunigt Konsolidierung dramatisch (z.B. 50 statt 500 Tage)
- **Überlagerung mehrerer Konsolidierungsschichten**: Porenwasserüberdrücke aus verschiedenen Lastanteilen addieren sich entlang der Gleitfuge
- **Isochronendarstellung**: Zeitabhängige Porenwasserdruckverteilung wird grafisch in der Bodenschicht dargestellt

## Typische Workflows

### Workflow 1: Damm mit Konsolidierung berechnen (Grundsystem)

1. `Datei > Neu` — EC7, Böschungsbruch, Lamellen, Porenwasserdrucklinie, Bemessungssituation BS-P
2. Geländeoberkante definieren (4 Punkte: linker Rand, Böschungsfuß, Böschungskrone, rechter Rand)
3. Bodenschichten definieren: Auffüllung (φ=30°, γ=19), Klei (φ=15°, c=11, γ=20), Sand (φ=30°, γ=19)
4. Wasserstände setzen: links 1 m (Vorflut), im Damm 2 m
5. Porenwasserdrucklinie definieren (Sickerlinie durch Damm)
6. Konsolidierungsschicht 1 definieren: Bereich der Kleischicht, Porenwasserüberdruck aus Auffüllungslast (11 kN/m² am Böschungsfuß unter Auftrieb, 19 kN/m² im Dammbereich erdfeucht)
7. Bodenkennwerte der Konsolidierungsschicht: Steifemodul (z.B. 1000 kN/m²), Durchlässigkeit (z.B. 10⁻¹⁰), Entwässerung oben+unten offen
8. Liegezeit = 0 (Zeitpunkt t=0)
9. Gleitkreismittelpunkte und Suchbereich definieren
10. Berechnen — Auslastung für Anfangszustand ablesen (z.B. 0,8)

### Workflow 2: Zusätzliche Verkehrslast als zweite Konsolidierungsschicht

1. Grundsystem wie Workflow 1
2. Verkehrslast definieren (z.B. 40 kN/m² auf 3 m Breite nahe Böschungskrone)
3. Zweite Konsolidierungsschicht definieren: Lastausbreitung berechnen (z.B. 3 m auf 9,60 m → 12,5 kN/m²), Schichtdicke und Porenwasserüberdruck eingeben
4. Konsolidierungsschicht 1: Liegezeit z.B. 500 Tage, Konsolidierungsschicht 2: Liegezeit 0 (spontane Verkehrslast)
5. Berechnen — Auslastung bei Überlagerung beider Porenwasserdruckanteile prüfen
6. Im Überlagerungsbereich addieren sich die Porenwasserüberdrücke (z.B. 19 + 12,5 = 31,5 kN/m²)

### Workflow 3: Bauablaufplanung mit Vertikaldrainagen

1. Grundsystem mit Konsolidierungsschichten wie Workflow 2
2. Feststellung: Nach 500 Tagen Auslastung gerade ≤ 1,0 — zu lange Wartezeit
3. Konsolidierungsschicht bearbeiten: Vertikaldrainage aktivieren (z.B. 0,5 m Abstand, 5 cm Drainradius)
4. Liegezeit auf z.B. 50 Tage reduzieren
5. Berechnen — Auslastung prüfen (deutlich unter 1,0 dank Drainage)
6. Isochronen prüfen: Über Schichthöhe nahezu gleiche Spannungen (horizontale Entwässerung zu Drainelementen)

## Fachbegriffe

| Begriff | Erklärung |
|---------|-----------|
| Konsolidierungsschicht | Geometrisch definierter Bereich, in dem Porenwasserüberdrücke durch Belastung entstehen — nicht an Bodenschichtgrenzen gebunden |
| Porenwasserüberdruck | Zusätzlicher Wasserdruck in wassergesättigtem, bindigem Boden durch aufgebrachte Last — dissipiert mit der Zeit |
| Isochrone | Linie gleicher Konsolidierungszeit — zeigt die Porenwasserdruckverteilung zu einem bestimmten Zeitpunkt |
| Konsolidierungsbeiwert cv | Bodenkennwert aus Steifemodul und Durchlässigkeit — bestimmt die Konsolidierungsgeschwindigkeit |
| Zeitpunkt t=0 | Physikalisch-theoretischer Zeitpunkt der spontanen Belastung — gesamte Last als Porenwasserüberdruck |
| Vertikaldrainage | Vertikale Dränelemente zur Verkürzung der horizontalen Entwässerungswege — beschleunigt Konsolidierung erheblich |
| Liegezeit | Zeitraum seit Aufbringen der Belastung — bestimmt den Grad der Konsolidierung |
| Entwässerungsbedingungen | Definition ob Schichtober-/unterkante durchlässig (offen) oder undurchlässig (geschlossen) ist |
| Lamellen | Vertikale Scheiben, in die der Gleitkörper für die Böschungsbruchberechnung unterteilt wird |
| Konsolidierungsspannung | Die durch eine Last erzeugte Spannung, die zum Zeitpunkt t=0 vollständig als Porenwasserüberdruck vorliegt |

## Häufige Fragen

- **Müssen Konsolidierungsschichten an Bodenschichtgrenzen liegen?**
  Nein. Konsolidierungsschichten sind unabhängig von Bodenschichten definierbar. Man kann auch mehrere Konsolidierungsschichten innerhalb einer Bodenschicht anlegen.

- **Woher kommen die Porenwasserüberdrücke als Eingabewerte?**
  Aus der Spannungsverteilung der aufgebrachten Last: Oberhalb des Grundwasserspiegels wirkt die Feuchtwichte (z.B. 19 kN/m²), unterhalb die Wichte unter Auftrieb (z.B. 11 kN/m²). Für Verkehrslasten kann eine vereinfachte Lastausbreitung angesetzt werden.

- **Wie unterscheidet sich die globale Konsolidierungszeit von der schichtspezifischen?**
  Die globale Zeit gilt für alle Konsolidierungsschichten gleichzeitig. Schichtspezifische Zeiten ermöglichen unterschiedliche Liegezeiten — wichtig bei gestaffelten Bauabläufen, wo verschiedene Lasten zu unterschiedlichen Zeitpunkten aufgebracht werden.

- **Wie helfen Vertikaldrainagen bei der Standsicherheit?**
  Vertikaldrainagen verkürzen die horizontalen Entwässerungswege, sodass die Konsolidierung erheblich schneller abläuft (im Beispiel: 50 statt 500 Tage bis zur ausreichenden Standsicherheit). Die Porenwasserüberdrücke dissipieren schneller, was die Standsicherheit früher gewährleistet.

## Quelle
- **Titel**: Wie berücksichtige ich Konsolidierungsprozesse bei den Berechnungen und Nachweisen zur Böschungsstabilität
- **Referent**: Prof. Uwe Glabisch (Hochschule Wismar)
- **Moderation**: Thomas Walkemeier (CivilServe GmbH)
- **Software**: GGU-Stability
