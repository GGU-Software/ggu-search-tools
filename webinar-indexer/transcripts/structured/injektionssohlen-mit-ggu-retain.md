# Injektionssohlen mit GGU-Retain — Webinar-Zusammenfassung

## Zusammenfassung
Das Webinar zeigt die Berechnung und den Nachweis einer Baugrube mit Injektionssohle (HDI-Sohle) in GGU-Retain. Anhand eines rückverankerten Spundwandsystems in mitteldicht gelagertem Sand wird demonstriert, wie die Injektionssohle über differenzierte Bodenkennwerte (aktiv/passiv), angepasste Bettungsmodule und den Nachweis gegen hydraulischen Grundbruch bzw. Auftrieb modelliert wird. Besonders wird auf die Regelung nach EB 62 eingegangen, wonach bei ausreichend undurchlässiger Injektionssohle (≥ 2 Zehnerpotenzen geringer als der umgebende Boden) auf den Nachweis des hydraulischen Grundbruchs verzichtet werden kann. Abschließend wird die Plausibilitätskontrolle über die Potentialdarstellung und den Vergleich mit einem Grundwassermodell gezeigt.

## Dialog-Navigation

### Editor 1
- `System einstellen` — Aktive und passive Bodenkennwerte differieren aktivieren
- `Baugrube` — Baugrubentiefe, Grundwasserstände (rechts/links), Flächenlast definieren
- `Böden` — Erweiterte Eingabe mit getrennten Kennwerten aktiv/passiv (γ, φ, c, δ), Durchlässigkeit, QSK, QC
- `Böden > Bodenfarben` — Getrennte Farbdarstellung auf der Passivseite (z.B. HDI-Sohle grau)
- `Art des Erddrucks` — Aktiver Erddruck nach DIN 4085
- `Wasser` — Stromröhre aktivieren für hydraulischen Gradienten im Passivbereich
- `Nachweise und Teilsicherheiten` — Bemessungssituation wählen (BS-P), Teilsicherheiten für hydraulischen Grundbruch/Auftrieb
- `Auftrieb und hydraulischer Grundbruch` — Beide Nachweise einzeln aktivierbar, Durchlässigkeit der Injektionssohle eingeben
- `Herausziehwiderstand` — Nachweis für Verpressanker

### Editor 2
- `Anker` — Neigung, Länge, Dehnsteifigkeit; Anker- und Steifenabstand verwenden (Eingabe in kN statt kN/m)
- `Bettungsmodule` — Schichtweise: Sand 10 MN/m³, HDI-Zone 50 MN/m³ (erzeugt steifenartige Auflagerung)
- `Bettungsmodule > Schichtgrenzen setzen` — Bettungsmodule automatisch an Bodenschichtgrenzen anpassen

### System
- `Berechnen` — Profillänge, Erddruckumlagerung nach EAB, Wasserdruck mit Stromröhre
- `Einstellungen Grafik` — Potentialdarstellung aktivieren für Plausibilitätskontrolle

## Kernfunktionen
- **Differenzierte Bodenkennwerte aktiv/passiv**: Injektionssohle nur auf der Passivseite mit erhöhtem Reibungswinkel und Kohäsion, Aktivseite bleibt Sand
- **Geteilte Bodenlegende**: Automatische Darstellung unterschiedlicher Böden links/rechts bei differierenden Kennwerten
- **Bodenfarben Passivseite**: Separate Farbzuweisung für Passivseite (z.B. HDI-Sohle in Grau) — neue Funktion
- **Erhöhter Bettungsmodul im HDI-Bereich**: 50 MN/m³ statt 10 MN/m³ erzeugt steifenartige Auflagerung ohne zusätzliche Steife
- **Hydraulischer Grundbruch vs. Auftrieb**: Beide Nachweise separat schaltbar; nach EB 62 kann bei ≥ 2 Zehnerpotenzen Durchlässigkeitsunterschied auf hydraulischen Grundbruch verzichtet werden
- **Potentialdarstellung**: Grafische Kontrolle der hydraulischen Verhältnisse, Vergleich mit Grundwassermodell möglich
- **Nachweis vertikale Tragfähigkeit**: Spitzendruck QC aus Drucksondierung für Spundwandnachweis
- **Anker in kN**: Über Schalter „Anker- und Steifenabstand verwenden" direkte Eingabe in kN statt kN/m

## Typische Workflows

### Workflow 1: Baugrube mit Injektionssohle berechnen

1. `System einstellen` — Aktive/passive Bodenkennwerte differieren aktivieren, Spundwand wählen
2. `Baugrube` — Tiefe 6 m, GW rechts -2 m, GW links -6,50 m (abgesenkt), Flächenlast 10 kN/m²
3. `Böden` — Sand (φ=32,5°, k=10⁻⁴) für alle Schichten; HDI-Sohle auf Passivseite: φ um 5° erhöht, c=100 kN/m²
4. `Bodenfarben` — HDI-Sohle auf Passivseite grau einfärben
5. `Wasser` — Stromröhre aktivieren
6. `Auftrieb und hydraulischer Grundbruch` — Beide Nachweise aktivieren, Durchlässigkeit HDI 10⁻⁷ eingeben
7. `Editor 2 > Anker` — Neigung 25°, Länge 10,80 m, Dehnsteifigkeit, QSK-Nachweis
8. `Bettungsmodule` — Sand 10 MN/m³, HDI-Zone 50 MN/m³
9. `Berechnen` — Profillänge 12 m (bis Unterkante Injektionssohle), Erddruckumlagerung nach EAB
10. Nachweise prüfen: Bemessung, vertikale Tragfähigkeit, Herausziehwiderstand, hydraulischer Grundbruch, Auftrieb

### Workflow 2: Injektionssohle optimieren (Dicke reduzieren)

1. Ausgangssystem wie Workflow 1 berechnen
2. Injektionssohle um 1,50 m anheben (Bodenschichtgrenzen anpassen)
3. `Bettungsmodule > Schichtgrenzen setzen` — Bettung automatisch anpassen
4. Profillänge entsprechend reduzieren
5. Berechnen — hydraulischer Grundbruch prüfen (ggf. nicht mehr nachweisbar)
6. Nach EB 62: Bei ≥ 2 Zehnerpotenzen Durchlässigkeitsunterschied (10⁻⁷ vs. 10⁻⁴ im Sand) → hydraulischen Grundbruch deaktivieren
7. Nur Auftriebsnachweis führen

### Workflow 3: Plausibilitätskontrolle über Potentialdarstellung

1. `Einstellungen Grafik` — Potential darstellen aktivieren
2. Bettungsmodul-Darstellung ausblenden
3. Potentialverlauf prüfen: Links Potential = GW-Stand (-2 m), rechts abgesenkt (-6,50 m), linearer Abbau über Injektionssohle
4. Optional: Vergleich mit GGU-2D SS-Flow (Grundwassermodell) — Abweichung im Promillebereich

## Fachbegriffe

| Begriff | Erklärung |
|---------|-----------|
| Injektionssohle (HDI-Sohle) | Künstlich hergestellte, wenig durchlässige Bodenschicht durch Hochdruckinjektion zur Abdichtung der Baugrubensohle |
| Hydraulischer Grundbruch | Versagen durch aufwärts gerichtete Strömungskräfte im durchlässigen Boden — erfordert strömendes Medium |
| Auftriebssicherheit | Nachweis, dass der Wasserdruck von unten die Gewichtskraft des Bodenkörpers nicht übersteigt |
| EB 62 | Empfehlung des Arbeitskreises Baugruben: Schicht gilt als annähernd wasserundurchlässig bei ≥ 2 Zehnerpotenzen geringerer Durchlässigkeit als umgebender Boden |
| Stromröhre | Berechnung des Wasserdrucks unter Berücksichtigung der Umströmung der Verbauwand (hydraulischer Gradient) |
| Bettungsmodul | Federsteifigkeit des Bodens (MN/m³); erhöhter Wert in HDI-Zone erzeugt steifenartige Auflagerung |
| QSK | Mantelreibung für den Nachweis des Anker-Herausziehwiderstands |
| QC | Spitzendruck aus der Drucksondierung für den Nachweis der vertikalen Tragfähigkeit der Verbauwand |
| Dehnsteifigkeit | Steifigkeit des Ankers in Achsrichtung (in kN), bestimmt die Verformung unter Last |
| Potentialdarstellung | Grafische Darstellung der hydraulischen Potentiale zur Plausibilitätskontrolle |

## Häufige Fragen

- **Wann kann auf den Nachweis des hydraulischen Grundbruchs verzichtet werden?**
  Nach EB 62: Wenn die Durchlässigkeit der Injektionssohle mindestens 2 Zehnerpotenzen geringer ist als die des umgebenden Bodens (z.B. HDI mit k=10⁻⁷ in Sand mit k=10⁻⁴).

- **Warum wird der passive Wandreibungswinkel auf -0,5 gesetzt?**
  Um den Nachweis des mobilisierten Erdwiderstands einzuhalten. Bei höheren Werten kann der Nachweis nicht geführt werden.

- **Warum ist der Bettungsmodul in der HDI-Zone höher?**
  Die Injektionssohle wirkt wie eine steife Auflagerung. Der erhöhte Bettungsmodul (50 statt 10 MN/m³) bildet diesen Effekt ab — eleganter als die Modellierung mit einer zusätzlichen Steife.

- **Wie überprüft man die Plausibilität der hydraulischen Berechnung?**
  Über die Potentialdarstellung in den Grafikeinstellungen. Der Potentialverlauf muss physikalisch sinnvoll sein (linearer Abbau über die Injektionssohle). Vergleich mit GGU-2D SS-Flow zeigt Abweichungen im Promillebereich.

## Quelle
- **Titel**: Injektionssohlen mit GGU-Retain
- **Referent**: [unklar, vermutlich Prof. Uwe Glabisch]
- **Software**: GGU-Retain
