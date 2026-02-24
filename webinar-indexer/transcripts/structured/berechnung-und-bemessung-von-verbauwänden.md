# Berechnung und Bemessung von Verbauwänden — Webinar-Zusammenfassung

## Zusammenfassung
Das Webinar zeigt die Berechnung und Bemessung von Spundwänden und Trägerbohlwänden mit GGU-Retain. Es werden die Unterschiede zwischen Global- und Teilsicherheitskonzept (DIN 1054) erläutert, die Erddruckumlagerung nach EAB/EAU vorgestellt und die Berücksichtigung von Ankern, Blocklasten, Bettung und Strömungsdruck demonstriert. Anhand eines Schritt-für-Schritt-Beispiels wird gezeigt, wie man ein System aufbaut, berechnet, bemisst und die Ergebnisse auswertet.

## Dialog-Navigation
- `Datei > Neu` — Dialogbox "Neuer Datensatz": Datensatzbeschreibung, Wahl zwischen Teilsicherheitskonzept (DIN 1054 neu) und Globalsicherheitskonzept (DIN 1054 alt), Schalter für absolute Höhen, aktive/passive Bodenkennwerte, Profilwerte, Wandart (Spundwand/Trägerbohlwand)
- `Editor 1` — Haupteingaben: System einstellen, Böden, Anker, Blocklasten, Bettungsmodule, Wasser, Nachweise und Teilsicherheiten
- `Editor 1 > System einstellen` — Baugrubentiefe, Grundwasserstand links/rechts, Flächenlast, Berme
- `Editor 1 > Böden` — Anzahl der Bodenschichten, Bodenkennwerte (Phi, Gamma, Kohäsion), Durchlässigkeit
- `Editor 1 > Anker` — Anzahl der Anker, Ankerlage (Tiefe unter Wandkopf), Neigung, Länge
- `Editor 1 > Blocklasten` — Vertikalanteil, Abstand zur Wand, Breite, Tiefe, Berücksichtigungsart (Dreieck mit Maximum oben), Lasttyp (Verkehrslast/ständig)
- `Editor 1 > Bettungsmodule` — Horizontale Bettungsmodule je Tiefenbereich
- `Editor 1 > Wasser` — Strömungsdruck auf aktiver/passiver Seite, Umströmung mit Stromnetz
- `Editor 1 > Nachweise und Teilsicherheiten` — Teilsicherheitsbeiwerte für Lastfall 1, 2 und 3, Standardwerte abrufbar
- `Editor 1 > Ankervorspannung` — Vorspannkraft je Anker
- `Editor 1 > Vorverformung einstellen` — Vorverformung von Hand oder aus Datei
- `Editor 2` — Weitere Einstellungsmöglichkeiten
- `System > System berechnen` — Berechnungsdialog: Einspanngrad, Erddruckumlagerung (EAB/EAU 2004), passiven Erddruck vorlagern, Theorie 2. Ordnung
- `System > System bemessen` — Profilwahl, Streckgrenze (Teilsicherheitskonzept) bzw. zul. Sigma/Tau (Globalsicherheitskonzept), bestes Profil suchen
- `System > Anker` — Ankerlänge nach Optimierung einsehen
- `System > Einstellungen Grafik` — Zustandsgrößen G+Q, G, Q einzeln ein-/ausblenden
- `System > Positionen` — Darstellungseinstellungen für Ergebnisse
- `Auswerten > Tiefe Gleitfuge` — Nachweis tiefe Gleitfuge, Ausnutzungsgrad, Optimierung der Ankerlänge
- `Auswerten > Summe V` — Nachweis der vertikalen Gleichgewichtskontrolle (charakteristische und Bemessungsgrößen)
- `Protokoll > Protokoll ausgeben` — Grafik und ASCII-Ausgabe, umfangreiche Dokumentation

## Kernfunktionen
- **Globalsicherheitskonzept / Teilsicherheitskonzept**: Jederzeit umschaltbar, Ergebnisse direkt vergleichbar. Beim Umschalten werden Teilsicherheitsbeiwerte automatisch angepasst.
- **Automatische Profilbemessung**: Das Programm sucht aus einer Profilliste das optimale Profil und bemisst es nach dem gewählten Konzept. Alternativ können benutzerdefinierte Profilwerte verwendet werden.
- **Erddruckumlagerung**: Verschiedene Umlagerungsfiguren nach EAB und EAU 2004 wählbar. Bei Rückverankerung oder Aussteifung ist eine Umlagerung erforderlich.
- **Vorlagern des passiven Erddrucks**: Beim Teilsicherheitskonzept zwingend; beim Globalsicherheitskonzept optional. Ohne Vorlagerung werden aktive und passive Erddruckordinaten unterhalb der Baugrubensohle addiert.
- **Stabwerksberechnung**: Hinter dem Programm steht ein Stabwerkssystem, das Anker als Stäbe (nicht als feste Auflagerpunkte) berücksichtigt. Interaktion zwischen Wand und Anker wird abgebildet.
- **Theorie 2. Ordnung**: Kann bei der Berechnung aktiviert werden, um Knickstabilität zu berücksichtigen.
- **Nachweis tiefe Gleitfuge**: Automatischer Nachweis mit Ausnutzungsgrad und Optimierungsfunktion für die Ankerlänge.
- **Summe-V-Nachweis**: Automatische Kontrolle der vertikalen Gleichgewichtsbedingung mit charakteristischen und Bemessungsgrößen nach EAB/EAU.
- **Bettungsmodulverfahren**: Bettungsmodule tiefenabhängig eingebbar, Vergleich Bettungspressung mit passivem Erddruck (charakteristisch oder mit Teilsicherheit).
- **Strömungsdruck / Stromnetz**: Berechnung der Umströmung der Wand mit Stromnetz unter Berücksichtigung unterschiedlicher Durchlässigkeiten je Bodenschicht.
- **Ankervorspannung und Vorverformung**: Vorspannkraft je Anker eingebbar; Vorverformung manuell oder aus vorheriger Berechnung (Datei) übernehmbar.
- **Ergebnisdarstellung**: Momente, Querkräfte, Normalkräfte und Verschiebungen grafisch dargestellt. Getrennte Darstellung von G, Q und G+Q. Per Doppelklick auf eine Stelle werden alle Bemessungswerte angezeigt.

## Typische Workflows

### Einfache Spundwandberechnung (Globalsicherheitskonzept)
1. `Datei > Neu` — Globalsicherheitskonzept wählen, Wandart "Spundwand" auswählen
2. `Editor 1` — Baugrubentiefe (z.B. 2 m), Grundwasserstand, Bodenkennwerte (Phi, Kohäsion) eingeben
3. `System > System berechnen` — Option "Passiven Erddruck vorlagern" setzen, Berechnung starten
4. `System > System bemessen` — zul. Sigma und zul. Tau vorgeben, "Bestes Profil suchen" aktivieren, OK
5. Ergebnisse prüfen: Momentenlinie, Querkraft, Normalkraft, Verschiebung, Einbindetiefe und erforderliche Länge

### Umschaltung auf Teilsicherheitskonzept und Vergleich
1. `Editor 1 > System einstellen` — Von Globalsicherheitskonzept auf Teilsicherheitskonzept umschalten
2. Teilsicherheitsbeiwerte in der erscheinenden Dialogbox prüfen (Standardwerte nach DIN 1054)
3. `System > System berechnen` — Berechnung starten (Vorlagerung ist automatisch aktiv)
4. `System > System bemessen` — Streckgrenze (z.B. 24 kN/cm² für S235) und Gamma-Stahl (1,1) prüfen, bestes Profil suchen
5. Ergebnisse vergleichen: Erforderliche Länge, Momente, Profilwahl

### Verankerte Spundwand mit Blocklast
1. `Editor 1` — Baugrubentiefe (z.B. 4 m), Grundwasserstand eingeben
2. `Editor 1 > Anker` — Anzahl auf 1 erhöhen, Ankerlage (z.B. 0,5 m unter Wandkopf), Neigung (z.B. 20°), Länge (z.B. 6,25 m) eingeben
3. `Editor 1 > Blocklasten` — Blocklast eingeben (z.B. 50 kN/m², Abstand 1 m, Breite 2 m, als Verkehrslast)
4. `System > System berechnen` — Einspanngrad wählen (1,0 = voll eingespannt, 0,0 = frei aufgelagert, Zwischenwerte = Teileinspannung), Erddruckumlagerung nach EAB wählen
5. Bemessung anschließen und Ergebnisse prüfen
6. `Auswerten > Tiefe Gleitfuge` — Ausnutzungsgrad prüfen, bei Überschreitung "Optimieren" klicken (Ankerlänge wird automatisch angepasst)

### Bettungsmodulverfahren mit Strömungsdruck
1. `Editor 1 > Bettungsmodule` — Horizontale Bettungsmodule je Tiefenbereich eingeben
2. `Editor 1 > Wasser` — Strömungsdruck aktivieren, ggf. Umströmung mit Stromnetz wählen
3. `Editor 1 > Böden` — Durchlässigkeiten je Bodenschicht eingeben
4. `System > System berechnen` — Berechnung starten (Hinweis: Bettungspressung wird mit charakteristischem oder abgemindertem passiven Erddruck verglichen, je nach Einstellung)
5. Ergebnisse prüfen: Differenzwasserdruckbild, Momentenlinie, Bettungspressung vs. passiven Erddruck

## Fachbegriffe

| Begriff | Erklärung |
|---|---|
| Globalsicherheitskonzept | Altes Bemessungskonzept nach DIN 1054 alt mit einer globalen Sicherheit (z.B. 1,5 auf passiven Erddruck) |
| Teilsicherheitskonzept | Neues Bemessungskonzept nach DIN 1054 neu mit getrennten Teilsicherheitsbeiwerten für Einwirkungen und Widerstände |
| Passiven Erddruck vorlagern | Getrennte Betrachtung von aktivem und passivem Erddruck unterhalb der Baugrubensohle (beim Teilsicherheitskonzept zwingend) |
| Erddruckumlagerung | Umverteilung des Erddrucks bei verankerten/ausgesteiften Wänden nach EAB- oder EAU-Figuren |
| EAB | Empfehlungen des Arbeitskreises Baugruben (Regelwerk für Baugrubenverbauwände) |
| EAU 2004 | Empfehlungen des Arbeitsausschusses Ufereinfassungen (Regelwerk für Hafenbau/Uferwände) |
| Einspanngrad | Grad der Fußeinspannung: 0 = frei aufgelagert, 1 = voll eingespannt, Zwischenwerte = Teileinspannung |
| Bettungsmodul | Federsteifigkeit des Bodens (horizontal), beschreibt den Zusammenhang zwischen Verschiebung und Bodenpressung |
| Tiefe Gleitfuge | Nachweis, dass der Anker mit ausreichender Länge hinter eine mögliche Gleitfläche reicht |
| Summe V | Nachweis des vertikalen Gleichgewichts der Verbauwand (alle Vertikalkräfte müssen nach unten abgetragen werden) |
| Stromnetz | Berechnung der Grundwasserumströmung der Wand zur Ermittlung des Strömungsdrucks |
| Theorie 2. Ordnung | Berechnungsmethode, die Verformungseinflüsse auf die Schnittgrößen berücksichtigt (Knickstabilität) |
| Streckgrenze | Bemessungswert der Stahlspannung im Teilsicherheitskonzept (z.B. 24 kN/cm² für S235) |
| Mantelreibung | Reibungswiderstand entlang der Wandfläche im Boden, relevant für den Summe-V-Nachweis |
| Spitzendruck | Vertikaler Widerstand am Fußpunkt der Wand zur Abtragung von Vertikalkräften |
| Lastfall 1, 2, 3 | Bemessungssituationen mit unterschiedlichen Teilsicherheitsbeiwerten (LF1 = ständig/vorübergehend, LF2 = außergewöhnlich, LF3 = Erdbeben) |
| G + Q | Schnittgrößen aus ständigen (G) und veränderlichen (Q) Einwirkungen |
| Bemessungsmoment (D) | Moment unter Berücksichtigung der Teilsicherheitsbeiwerte: M_G × γ_G + M_Q × γ_Q |

## Häufige Fragen

**Wie bestimmt man die Ankerlänge?**
Die Ankerlänge wird zunächst vom Benutzer vorgegeben. Nach der Berechnung kann über `Auswerten > Tiefe Gleitfuge > Optimieren` die optimale Ankerlänge automatisch ermittelt werden. Die optimierte Länge wird dann unter `System > Anker` eingetragen.

**Ist eine Teileinspannung möglich?**
Ja, der Einspanngrad ist stufenlos wählbar zwischen 0 (frei aufgelagert) und 1 (voll eingespannt). Werte dazwischen ergeben eine Teileinspannung. Eine Teileinspannung führt zu einem kleineren Feldmoment, erfordert aber eine längere Wand.

**Kann eine Ankervorspannkraft eingegeben werden?**
Ja, unter `Editor 1 > Ankervorspannung` kann jedem Anker eine Vorspannung zugewiesen werden.

**Wie wird Vorverformung berücksichtigt?**
Unter `Editor 1 > Vorverformung einstellen` kann Vorverformung manuell eingegeben oder aus einer Datei eines vorherigen Aushubzustands übernommen werden. Die Vorverformung wird nicht automatisch zwischen Aushubzuständen weitergegeben, sondern muss über die Dateiwahl übertragen werden.

**Wird Knickstabilität berücksichtigt?**
Ja, bei der Berechnung kann Theorie 2. Ordnung aktiviert werden. Das zugrunde liegende Stabwerkssystem berücksichtigt die Interaktion zwischen Wand und Anker, einschließlich der Normalkrafteinleitung durch geneigte Anker.

**Wie wird die Fußbettung bei Festgestein (z.B. Trägerbohlwand) simuliert?**
Unter `Editor 1 > Bettungsmodule` wird für den Festgesteinsbereich ein entsprechend hoher Bettungsmodul eingegeben.

**Wird Summe V automatisch kontrolliert?**
Ja, die vertikale Gleichgewichtskontrolle erfolgt automatisch. Es werden zwei Nachweise geführt: (1) Summe aller Vertikalkräfte unter charakteristischen Größen muss nach unten gerichtet sein, (2) unter Bemessungsgrößen muss der Spitzendruck ausreichend sein. Bei Nichterfüllung erfolgt ein Hinweis.

**Wie wird Strömungsdruck berücksichtigt?**
Unter `Editor 1 > Wasser` kann Strömungsdruck auf aktiver und/oder passiver Seite aktiviert werden. Zusätzlich kann eine Umströmung mit Stromnetz berechnet werden, wobei Durchlässigkeiten je Bodenschicht unter `Editor 1 > Böden` definiert werden.

**Warum wird die Spundwand beim Teilsicherheitskonzept länger?**
Beim Globalsicherheitskonzept liegt die Sicherheit nur auf dem passiven Erddruck (ca. 1,5). Beim Teilsicherheitskonzept werden sowohl die Einwirkungen erhöht (γ_G = 1,35, γ_Q = 1,5) als auch der Erdwiderstand abgemindert (γ_Ep = 1,4). Das ergibt eine rechnerische Gesamtsicherheit von ca. 1,96, was zu längeren Profilen führt. Bei Lastfall 2 (γ_G = 1,2, γ_Q = 1,3, γ_Ep = 1,3) ergibt sich wieder ca. 1,5 wie beim alten Konzept.

**Was ändert sich bei der Bettung im Teilsicherheitskonzept?**
Nach neuer Normung dürfen die Einzelwerte der Bettungspressung mit den charakteristischen Werten des passiven Erddrucks verglichen werden (statt mit den abgeminderten Werten). Nur die Summe der Auflagerreaktion muss kleiner sein als die Summe des passiven Erdwiderstands geteilt durch die Teilsicherheit. Dies kann eine Einsparung von ca. 25 % beim Moment ergeben.

## Quelle
- **Titel**: Berechnung und Bemessung von Verbauwänden
- **Referent**: [unklar]
- **Software**: GGU-Retain
