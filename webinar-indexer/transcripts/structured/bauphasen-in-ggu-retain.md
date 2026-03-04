# Bauphasen in GGU-Retain — Webinar-Zusammenfassung

## Zusammenfassung
Das Webinar zeigt, wie verschiedene Bauphasen bei der Berechnung und den Nachweisen von Verbauwänden mit GGU-Retain berücksichtigt werden. Anhand eines Beispiels einer 10 m tiefen, doppelt verankerten Baugrube mit Schlitzwand werden vier Bauphasen (Voraushub, einfache Verankerung, doppelte Verankerung, Rückbau) nacheinander berechnet. Die Ergebnisse werden überlagert, um umhüllende Zustandsgrößen für die Bemessung zu erhalten. Besonderer Fokus liegt auf dem Rückbauzustand mit Verfüllung, Gebäudelast und reduziertem Erdwiderstand.

## Dialog-Navigation
- `Datei > Neu` — Neuen Datensatz anlegen, Schlitzwand auswählen
- `Datei > Speichern unter` — Bauphase separat speichern (jede Phase als eigene Datei)
- `Editor 1 > Baugrube` — Baugrubentiefe, Grundwasserstände einstellen
- `Editor 1 > Böden` — Bodenschichten, Kennwerte (Wichte, Reibungswinkel, Kohäsion) definieren
- `Editor 1 > Böden > Bodenfarben` — Farbdarstellung je Bodenschicht (aktiv/passiv getrennt)
- `Editor 1 > Bettungsmodule` — Bettungsprofil definieren (linear ansteigend, schichtabhängig)
- `Editor 1 > Anker` — Anzahl, Tiefe, Neigung, Länge, Verpresskörperlänge der Anker
- `Editor 1 > Zweiseitige begrenzte Lasten` — Oberflächenlasten auf Aktiv- oder Passivseite
- `Editor 1 > Nachweise und Teilsicherheiten` — Bemessungssituation (BS-T) einstellen
- `Editor 1 > Vergleichsfuge` — Wandreibungswinkel auf Ersatzankerwand zu 0 setzen
- `System > Einstellen` — Aktive und passive Bodenkennwerte getrennt aktivieren
- `System > Berechnen` — Einspanngrad, Profillänge fest/automatisch, Erddruckumlagerung
- `System > Berechnen > Profillänge fest und Fuß gebettet` — Feste Verbauwandlänge mit Bettung
- `System > Bauphasen > Dateien` — Berechnete Phasendateien einladen für Überlagerung
- `System > Bauphasen > Darstellen` — Umhüllende der Zustandsgrößen zeichnen
- `System > Einstellungen Grafik` — Darstellung von Moment, Querkraft, Bewehrung konfigurieren
- `Editor 2 > Vorverformung einstellen` — Vorverformung für Sanierung berücksichtigen
- `Editor 2 > Vorverformung Info` — Vorverformung aus Datei oder von Hand eingeben
- `F9` — System auf Bildschirm zentrieren

## Kernfunktionen
- **Gebettetes System**: Berechnung mit Bettungsmodulen statt Blum-Verfahren — ermöglicht durchgängige Berechnung aller Bauphasen mit gleicher Wandlänge
- **Bauphasen-Überlagerung**: Einzeln berechnete Phasen werden überlagert, um umhüllende Zustandsgrößen (Moment, Querkraft, Normalkraft, Verschiebung) und Bewehrungsverlauf zu erhalten
- **Unterschiedliche Bodenkennwerte aktiv/passiv**: Für Rückbauzustände mit Verfüllung können auf der Passivseite reduzierte Kennwerte (geringerer Reibungswinkel) angesetzt werden
- **Erddruckumlagerung nach EAB**: Automatische Auswahl der Umlagerungsfigur für verankerte Systeme
- **Automatische Profillängenbestimmung**: Programm ermittelt erforderliche Verbauwandlänge
- **Bemessung Schlitzwand**: Bewehrungsführung (Längs- und Schubbewehrung), Luft-/Erdseite
- **Abrostungssimulation**: Für bestehende Spundwände können reduzierte Querschnittswerte berücksichtigt werden

## Typische Workflows

### Workflow 1: Bauphasen einer doppelt verankerten Baugrube berechnen

1. **Phase 3 zuerst berechnen** (maßgeblich für Wandlänge): Datei neu > Schlitzwand > Baugrube 10 m > 2 Anker > Bettung definieren > System berechnen mit automatischer Profillänge
2. Ermittelte Wandlänge merken (z.B. 12,90 m)
3. **Phase 1** (Voraushub 3 m): Phase 3 duplizieren > Baugrube auf 3 m > Anker entfernen > Bettung anpassen > Profillänge fest 12,90 m > ohne Umlagerung berechnen
4. **Phase 2** (einfach verankert, 7 m): Phase 1 duplizieren > Baugrube auf 7 m > 1 Anker > Bettung anpassen > Profillänge fest > mit Umlagerung berechnen
5. **Phase 4** (Rückbau): Phase 3 laden > Baugrubensohle auf 7 m hochziehen > 1 Anker entfernen > 4 Bodenschichten mit Verfüllung (passive Seite: reduzierter Reibungswinkel 25°) > Gebäudelast als Differenzlast auf Passivseite > Bettung anpassen > berechnen
6. Jede Phase separat abspeichern

### Workflow 2: Bauphasen überlagern und auswerten

1. Neue Datei anlegen oder letzte Phase verwenden
2. `System > Bauphasen > Dateien` — alle vier Phasendateien einladen
3. Gewünschte Phasen auswählen (z.B. erst 1-2, dann 1-4)
4. `Darstellen` klicken — umhüllende Zustandsgrößen werden gezeichnet
5. Bewehrungsverlauf (Längs- und Schubbewehrung) aus Umhüllender ablesen

### Workflow 3: Rückbauzustand modellieren

1. Baugrubensohle auf Verfüllungshöhe hochziehen (z.B. 7 m statt 10 m)
2. Bodenschichten erweitern: Verfüllung als eigene Schicht mit reduzierten Kennwerten auf Passivseite
3. Gebäudelast als Differenzlast auf Passivseite (Gesamtlast minus Eigengewicht Verfüllung)
4. Bettung im Verfüllbereich reduzieren
5. Oberen Anker kappen (Anzahl reduzieren)
6. System berechnen — Ankerkraft im verbleibenden Anker prüfen (kann deutlich höher sein)

## Fachbegriffe

| Begriff | Erklärung |
|---------|-----------|
| Bauphase | Einzelner Bauzustand (Aushub, Verankerung, Rückbau), der separat berechnet wird |
| Rückbauzustand | Phase nach Fertigstellung des Bauwerks: Anker gekappt, Arbeitsraum verfüllt |
| Gebettetes System | Berechnung mit Bettungsmodulen (W × K) statt klassischem Blum-Verfahren |
| Bettungsmodul | Federsteifigkeit des Bodens (kN/m³), schichtweise definiert, darf Erdwiderstand nicht überschreiten |
| Erddruckumlagerung | Umverteilung des Erddrucks bei verankerten Wänden nach EAB |
| Umhüllende | Einhüllende Kurve der Zustandsgrößen aus allen Bauphasen für die Bemessung |
| Profillänge fest | Verbauwandlänge aus maßgeblicher Phase wird für alle anderen Phasen übernommen |
| BS-T | Bemessungssituation temporär (für Baugruben) |
| Vergleichsfuge | Nachweis mit Wandreibungswinkel δ = 0 auf Ersatzankerwand (nach EAB/EAU) |
| Vorverformung | Bereits eingetretene Verformung einer bestehenden Wand, relevant bei Sanierung |
| Abrostung | Querschnittsminderung bei Stahlspundwänden durch Korrosion über die Standzeit |

## Häufige Fragen

- **Kann man in verschiedenen Bauphasen unterschiedliche Verbaulängen berücksichtigen?**
  Ja, technisch möglich. Sinnvoll ist es aber, die Länge aus der maßgeblichen Phase (meist Endaushub) für alle Phasen zu verwenden, da die Wand vor Baubeginn hergestellt wird.

- **Wie simuliert man die Sanierung einer 40 Jahre alten Spundwand mit nachträglicher Verankerung?**
  Abrostung über die Profildatenbank simulieren (reduzierte Querschnittswerte). Vorverformung über `Editor 2 > Vorverformung einstellen` berücksichtigen. Dann nachträgliche Verankerung modellieren.

- **Warum beginnt man mit Phase 3 statt Phase 1?**
  Phase 3 (doppelt verankert, volle Aushubtiefe) ist maßgeblich für die erforderliche Wandlänge. Diese Länge wird dann für alle anderen Phasen als feste Profillänge übernommen.

- **Warum ist die Ankerkraft im Rückbauzustand höher als im Bauzustand?**
  Durch Wegfall des zweiten Ankers und reduzierte Stützung durch die Verfüllung (geringerer Erdwiderstand) steigt die Beanspruchung des verbleibenden Ankers (im Beispiel: +23%, von 89,9 auf 111,5 kN/m).

## Quelle
- **Titel**: Bauphasen in GGU-Retain
- **Referent**: Prof. Uwe Glabisch (Hochschule Wismar)
- **Moderation**: Thomas Walkemeier (CivilServe GmbH)
- **Software**: GGU-Retain
