# GGU-SLAB — Webinar-Zusammenfassung

## Zusammenfassung
Das Webinar gibt eine Einführung in die Berechnung elastisch gebetteter Platten mit GGU-SLAB. Es werden beide Berechnungsverfahren vorgestellt: das Bettungsmodulverfahren (mit konstantem und variablem Bettungsmodul über Interpolationsnetz) und das Steifemodulverfahren (mit iterativem Abgleich zwischen Plattendurchbiegung und Halbraumsetzung). Zusätzlich wird die Berücksichtigung von Rüttelstopfverdichtung nach Priebe und Einzelpfählen demonstriert. Anhand einfacher Beispiele werden FE-Netz-Erzeugung, Belastung, Berechnung, Bewehrungsermittlung und Ergebnisauswertung gezeigt.

## Dialog-Navigation
- `Datei > Neu` — Neues System anlegen, Bettungsmodul- oder Steifemodulverfahren wählen
- `FE-Netz > Knoten > Ändern > Tabelle` — Knotenkoordinaten tabellarisch eingeben
- `FE-Netz > Netz von Hand` — Elemente manuell durch Knotenklick erzeugen, Materialzuordnung
- `FE-Netz > Raster > Regelmäßig > Rechteck` — Regelmäßiges Rechtecknetz generieren (Unterteilung wählbar)
- `FE-Netz > Raster > Regelmäßig > Viereck` — Unregelmäßiges Vierecknetz über Eckkoordinaten
- `FE-Netz > Raster > Kreis/Kreisring` — Kreis- und Kreisringplatten generieren
- `FE-Netz > Verfeinern` — Netz mehrfach verfeinern für genauere Ergebnisse
- `FE-Netz > Löschen` — Elemente entfernen für Aussparungen
- `System > Material Platte` — Plattenmaterialien definieren (Name, Dicke)
- `System > Testen` — FE-Netz auf Knotenabstände und Überlappungen prüfen
- `System > Berechnen` (oder `F5` oder Taschenrechner-Icon) — Berechnung starten
- `System > Platte bewehren` — Bewehrungsermittlung nach EC2 (Beton-/Stahlsorte wählbar)
- `Bettung > Standard-Bettung` — Konstanten Bettungsmodul für alle Knoten setzen
- `Bettung > Interpolationsnetz` — Variables Bettungsfeld über Hilfsnetz definieren
- `Bettung > Interpolationsnetz > Knoten setzen` — Stützpunkte mit bekannten Bettungswerten platzieren
- `Bettung > Interpolationsnetz > Netz erzeugen` — Elemente zwischen Stützpunkten verbinden
- `Bettung > Interpolationsnetz > Knoten ändern` — Bettungswerte je Knoten zuweisen
- `Bettung > Zuweisen` — Interpolierte Bettungswerte auf FE-Knoten übertragen
- `Bettung > Isolinien Bettung` — Kontrollanzeige der zugewiesenen Bettungswerte
- `Steifemodul > Einstellungen` — Verfahren konfigurieren, Rüttelstopfverdichtung aktivieren
- `Steifemodul > Schichten` — Bodenschichten mit Steifemodulen, Wichten definieren
- `Steifemodul > Standardtiefen` — Einheitliche Schichttiefen für alle Aufschlüsse
- `Steifemodul > Knoten setzen` — Bohrpunkte/Aufschlussorte platzieren
- `Steifemodul > Knoten editieren > Schichttiefen` — Individuelle Schichttiefen je Aufschluss
- `Steifemodul > Netz` — Bodenaufschlüsse zu Interpolationsnetz verbinden
- `Flächenlasten` — Lasten flächig oder materialweise zuweisen
- `Rand > Einzelfedern` — Pfähle als Einzelfedern an Knoten definieren
- `Auswerten > Isolinien > Verschiebung` — Setzungsbild als Isoflächenplot
- `Auswerten > Isolinien > Moment XX/YY` — Momentenverteilung
- `Auswerten > Isolinien > Pressung` — Bodenpressung unter der Platte
- `Auswerten > 3D` — Räumliche Darstellung der Biegelinie
- `Auswerten > Beliebiger Schnitt > Verschiebung` — Setzung entlang einer Schnittlinie
- `Auswerten > Bewehrung > Oben/Unten > Beschriften` — Bewehrungsbedarf (cm²/m) an Knoten

## Kernfunktionen
- **Bettungsmodulverfahren**: Konstante oder variable Bettung über Interpolationsnetz, jedem FE-Knoten individuell zuweisbar
- **Steifemodulverfahren**: Iterativer Abgleich von Plattendurchbiegung und Halbraumsetzung, Grenztiefenbestimmung am Plattenschwerpunkt
- **Interpolationsnetz**: Hilfsnetz zur flächigen Interpolation von Bettungs- oder Steifemodulen aus punktuellen Bodenaufschlüssen auf FE-Knoten
- **Rüttelstopfverdichtung nach Priebe**: Bodenverbesserung über Flächenverhältnis (Säule/Zelle) und E-Modul-Verhältnis, automatische Verbesserungsfaktorberechnung
- **Einzelpfähle als Federn**: Pfähle über Federkonstante (äußere + innere Tragfähigkeit) an Knoten modellierbar
- **Zugbettung unterbinden**: Verhindert unrealistische Zugkräfte zwischen Platte und Boden bei Plattenabhebung
- **FE-Netz-Generatoren**: Rechteck, Viereck, Kreis, Kreisring — automatische Netzerzeugung mit einstellbarer Verfeinerung
- **Bewehrungsermittlung nach EC2**: Oben/Unten in X/Y-Richtung, verschiedene Beton- und Stahlsorten, Mindestbewehrung

## Typische Workflows

### Workflow 1: Bettungsmodulverfahren mit konstanter Bettung
1. `Datei > Neu` — Bettungsmodulverfahren, Teilsicherheitskonzept
2. Knoten tabellarisch eingeben oder per Raster-Generator erzeugen
3. FE-Netz von Hand oder automatisch generieren, Materialzuordnung
4. `Material Platte` — Plattendicken definieren
5. `Standard-Bettung` — Bettungsmodul für alle Knoten setzen (z.B. 2500 kN/m³)
6. Flächenlasten zuweisen (über Material oder manuell)
7. FE-Netz verfeinern (2-3×)
8. `System testen` — Geometrie prüfen
9. Berechnen mit "Zugbettung unterbinden"
10. `Platte bewehren` nach EC2
11. Ergebnisse auswerten: Verschiebung, Momente, Pressung, Bewehrung

### Workflow 2: Bettungsmodulverfahren mit Interpolationsnetz
1. System wie Workflow 1 aufbauen (Schritte 1-7)
2. `Bettung > Interpolationsnetz` — Stützpunkte mit bekannten Bettungswerten setzen
3. Netz zwischen Stützpunkten erzeugen
4. Bettungswerte je Knoten zuweisen
5. `Bettung zuweisen` — Werte auf FE-Netz übertragen
6. `Isolinien Bettung` — Kontrolle der zugewiesenen Werte
7. Berechnen und auswerten

### Workflow 3: Steifemodulverfahren mit Bodenaufschlüssen
1. `Datei > Neu` — Steifemodulverfahren
2. FE-Netz per Raster-Generator erzeugen
3. `Steifemodul > Schichten` — Bodenschichten mit Steifemodulen definieren
4. `Standardtiefen` — Einheitliche Schichtunterkanten setzen
5. Aufschlusspunkte setzen, individuelle Schichttiefen editieren
6. Steifemodul-Netz erzeugen (Aufschlüsse verbinden)
7. Material und Lasten zuweisen
8. Berechnen (iterativ) — Zugbettung unterbinden
9. Bewehren und auswerten

### Workflow 4: Rüttelstopfverdichtung ergänzen
1. Steifemodulverfahren wie Workflow 3 aufbauen
2. `Steifemodul > Einstellungen` — Rüttelstopfverdichtung aktivieren
3. `Steifemodul > Schichten` — Flächenverhältnis und E-Modul-Verhältnis je Schicht eingeben
4. Berechnen — Verbesserungsfaktor wird automatisch ermittelt und in Bodenlegende angezeigt

## Fachbegriffe

| Begriff | Erklärung |
|---------|-----------|
| Bettungsmodulverfahren | Platte auf Winkler-Federn: jeder Knoten erhält einen Bettungsmodul (kN/m³) |
| Steifemodulverfahren | Iterativer Abgleich zwischen Plattendurchbiegung und Setzung des elastischen Halbraums |
| Interpolationsnetz | Hilfsnetz zur flächigen Verteilung von Bodenkennwerten auf FE-Knoten |
| Rüttelstopfverdichtung | Bodenverbesserung durch Schottersäulen nach Priebe, Verbesserungsfaktor aus Flächen-/E-Modul-Verhältnis |
| Zugbettung | Unrealistische Zugkräfte zwischen Platte und Boden — muss unterbunden werden |
| Grenztiefe | Tiefe, ab der die Zusatzspannung vernachlässigbar wird (Setzungsberechnung) |
| Einzelfedern | Modellierung von Pfählen als Federkonstante an FE-Knoten |
| Federkonstante (Pfahl) | Inverswert aus äußerer Tragfähigkeit (Widerstand-Setzungsdiagramm) + Dehnsteifigkeit |
| Isoflächenplot | Farbige Flächendarstellung von Ergebnisgrößen (Setzung, Momente, Pressung) |

## Häufige Fragen

- **Kann man Rüttelstopfverdichtung auch beim Bettungsmodulverfahren einsetzen?**
  Nicht direkt — die Rüttelstopfverdichtung wirkt über den Steifemodul (Verbesserungsfaktor). Beim Bettungsmodulverfahren müsste die Verbesserung über Umwege in den Bettungsterm einfließen.

## Quelle
- **Titel**: Einstieg in die Berechnung von elastisch gebetteten Platten mit GGU-SLAB
- **Referent**: Prof. Uwe Glabisch (Hochschule Wismar)
- **Moderation**: Thomas Walkemeier (CivilServe GmbH)
- **Software**: GGU-SLAB
