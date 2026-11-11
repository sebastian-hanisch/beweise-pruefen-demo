# Beweise schreiben und prüfen – „unerfüllbar“ glauben, weil ein zweites Programm nachrechnet – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-beweise-pruefen-demo.streamlit.app/)** -->

Sechstes Stück der Linie **SAT und Constraint Programming** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Die Vorgänger-Stücke zeigen, wie ein SAT-Löser eine Antwort **findet**; diese Demo zeigt, wie man sie **belegt** (bewusster Kontrast, keine Verbesserung des Lösers): Der Löser schreibt jede gelernte Klausel in ein Protokoll, und ein zweites, viel einfacheres Programm rechnet jede Zeile nach. Aufgaben sind das Schubfach (h + 1 Tauben in h Löchern), Zufalls-3-SAT und ein Handbeispiel mit drei Tauben und zwei Löchern, das sich von Hand nachrechnen lässt.

## Warum dieses Problem

Ein Löser, der „unerfüllbar“ sagt, hat nichts bewiesen, solange niemand nachrechnet. Bei „erfüllbar“ ist es einfach: Das Modell ist ein Zeuge, und ein Programm von einer Zeile prüft es. Bei „unerfüllbar“ gibt es keinen so kurzen Zeugen; hier hilft ein **Protokoll**, in dem jede Zeile eine Klausel ist, die aus der Formel und den Zeilen davor durch **Einheitspropagation** folgt, und dessen letzte Zeile die **leere Klausel** ist. Die Demo beantwortet vier Fragen mit Zählungen: **Wie prüft man einen Beweis Zeile für Zeile?** **Wie groß wird er?** **Nimmt der Prüfer je etwas an, das nicht folgt?** (Prüfer prüfen) und **Was ändern Löschzeilen?**

## Modell

- **Formel und Protokoll.** Eine Formel in konjunktiver Normalform; Literale sind ganze Zahlen (+v wahr, −v falsch). Ein Protokoll ist eine Folge von Zeilen `a Klausel` (hinzufügen) und `d Klausel` (löschen); bei „unerfüllbar“ endet es mit `a ()`. Das Format ist ein **RUP-Protokoll mit Löschzeilen** (eigene Messung), kein DRAT und kein LRAT.
- **Prüfer.** Für jede Zeile `a C`: Annahme, dass alle Literale von `C` falsch sind; Einheitspropagation auf den lebenden Klauseln (Formel plus bisher geprüfte Zeilen minus gelöschte) bis zum Fixpunkt; ein Widerspruch beweist die Zeile (**RUP**, reverse unit propagation). Der Beweis ist akzeptiert, wenn jede Zeile bis zur leeren Klausel so geprüft ist. Der Prüfer **zählt statt zu suchen** (Zähler statt beobachteter Literale) und ist deshalb mit Absicht langsam: Gezählt werden **Prüfschritte**, das sind angesehene Klauseln.
- **Wahrheit.** Eine Klausel `C` folgt aus `F`, wenn „`F` plus verneinte `C`“ unerfüllbar ist; die Demo bestimmt das unabhängig vom Prüfer durch Aufzählung aller Belegungen (bis 14 Variablen) oder durch den Löser (darüber). RUP ist **strenger** als Folgerung: Der Prüfer lehnt manche gefolgerte Klausel ab, nimmt aber (in den gemessenen Reihen) keine nicht gefolgerte an.
- **Hinweise (Ausblick).** Eine Hinweisliste nennt die Nummern der Klauseln, die nacheinander ein Literal erzwingen und zuletzt den Widerspruch liefern; ein Hinweisprüfer liest sie der Reihe nach und sucht nicht. Das ist die Idee hinter LRAT (Cruz-Filipe u. a. 2017, Volltext gelesen), aber die Syntax der Demo ist frei gewählt und **kein LRAT-Format**.
- Mathematik, Lesehilfe und Symboltabelle: Expander **📐 Mathematische Formulierung** in der App.

## Methodik

| Baustein | Datei | Anmerkung |
|---|---|---|
| Löser mit Protokoll (`proof=True`) | `bwp_cdcl.py` | wörtliche **Kopie** des Kern-Pakets der Linie (Kern-Version 832b2c10dfdea62d), nur der Import des Geschwistermoduls umgestellt; `tests/test_copies.py` prüft den Hash |
| Prüfer (Kopie des Kerns) | `bwp_rup.py` | **Kopie** (Kern-Version 885e1c74ce170cd5): `ist_rup`, `pruefe_beweis`; kein Import aus dem Löser |
| SplitMix64, Formelerzeuger | `bwp_rng.py`, `bwp_instanzen.py` | **Kopien** (Kern-Version 5d5d8f45d0e1eddf bzw. 6795de796b66fff8); nie Python-`random` oder `hash()` |
| Prüfer mit Erklärung | `bwp_pruefer.py` | eigener Code der Demo, ebenfalls ohne Import aus dem Löser (Quelltextprüfung): Kette der Einheiten je Zeile, Zeilennummer der Ablehnung, Hinweis auf Löschzeilen ohne Klausel, Hinweise und Hinweisprüfer; zählt dieselben Prüfschritte wie `bwp_rup.py` (Test) |
| Löser-Anbindung, Wahrheit, Solidität, Manipulation, Messzeilen | `bwp_algorithm.py` | `lauf`, `Wahrheit`, `soliditaet`, `manipuliere`, `messreihe_zufall`, `messreihe_schubfach`, `hinweis_beispiel` |
| Formeln und Schreibweise | `bwp_scenario.py` | Handbeispiel PHP(2), erfüllbare Formel G, Zufalls-3-SAT, Schubfach, Klauseleingabe |
| Verdikte, Tabellen, vorgerechnete Zeilen | `bwp_evaluation.py` | alle Verdikte als reine Funktionen; die Zahl in jedem Text stammt aus der Messung |
| Vorgerechnete Zeilen | `bwp_messreihen.json`, `tools/messreihen.py` | **vorgerechnet, nicht live**: Schubfach h = 7 (mit und ohne Löschzeilen, Konfliktbudget 100.000) und Zufalls-3-SAT n = 60, 70, 80 |

Experimente in der App (Reiter): **Zeile für Zeile prüfen** (Regler „Zeile“ blättert durch das Protokoll, je Zeile die angenommenen Literale, die Kette der Einheiten und der Widerspruch), **Beweisgröße** (Messreihe auf Knopfdruck), **Prüfer prüfen** (eigene Klausel, Vierfeldertafel an G und an 25 Zufallsformeln, Protokoll manipulieren) und **Löschzeilen und Schubfach** (Messreihe auf Knopfdruck); dazu der Reiter **Ausblick: DRAT, LRAT, CP-Beweise** mit Zitaten und der Hinweisrechnung des Handbeispiels. Schnellstart und allgemeine Einstellungen stehen in der Seitenleiste. Die Zufallsformel der Seitenleiste ist die **erste unerfüllbare** Formel ab dem gewählten Zufalls-Seed (m = 4,26 n Klauseln, gerundet).

## Befunde (gemessen, keine Behauptungen)

Messreihen: Beweisgröße je n die ersten 20 unerfüllbaren Zufalls-3-SAT-Formeln ab Zufalls-Seed 7000 (SplitMix64, ohne Löschzeilen); Schubfach eine Formel je h; Solidität 25 feste Formeln mit n = 30 und m = 100 (Zufalls-Seeds 1200 bis 1224), je Formel bis zu 60 Kandidatenklauseln. Gezählt wird nur in Konflikten, Zeilen, Prüfschritten und Propagationen des Lösers; Sekunden sind kein Befund.

| Frage | Befund | Test |
|---|---|---|
| **Handbeispiel PHP(2)**, Beweis von Hand (Zeilen A bis E) | Der Prüfer akzeptiert alle fünf Zeilen; Prüfschritte je Zeile 12 / 13 / 13 / 14 / 14, zusammen 66 (von Hand ausgezählt). Der Löser selbst schreibt einen kürzeren Beweis: zwei Zeilen `a (¬x2)` und `a ()` bei 2 Konflikten, 44 Prüfschritte. | `test_pruefschritte_des_handbeispiels_von_hand_ausgezaehlt`, `test_claim_handbeispiel_beweis_a_bis_e`, `test_claim_handbeispiel_loeser_schreibt_zwei_zeilen_mit_44_pruefschritten` |
| **Löschzeile** im Handbeispiel | Wird die Klausel 4 = (¬x1 ∨ ¬x3) vor Zeile C gelöscht, lehnt der Prüfer die Zeile C ab (Zeile 4 des Protokolls). Ohne sie erzwingt x1 nur ¬x4, x3, ¬x5, x6 und ¬x2; danach ist keine Klausel verletzt. | `test_loeschzeile_klausel_4_vor_zeile_c_macht_c_unbeweisbar`, `test_claim_handbeispiel_loeschzeile_klausel_4_macht_zeile_c_unbeweisbar` |
| **Solidität an G** (PHP(2) ohne (x3 ∨ x4) und (x5 ∨ x6), erfüllbar, 7 Modelle von 64; alle 60 Klauseln aus zwei Literalen über verschiedenen Variablen) | 15 akzeptiert und gefolgert, **0 akzeptiert und nicht gefolgert**, 0 abgelehnt und trotzdem gefolgert, 45 abgelehnt und nicht gefolgert. Die Klausel A = (¬x1 ∨ ¬x4), die in PHP(2) bewiesen wird, lehnt der Prüfer in G ab: sie folgt in G nicht (Modell mit x1 und x4 wahr). | `test_claim_solidaet_g_sieben_modelle_und_15_0_0_45`, `test_g_hat_sieben_modelle_und_die_klausel_a_folgt_nicht` |
| **Solidität an Zufallsformeln** (n = 30, m = 100; alle 25 Formeln erfüllbar; Wahrheit durch den Löser) | 857 Kandidaten: zufällige 2- und 3-Klauseln (749): 20 akzeptiert und gefolgert, **0 akzeptiert und nicht gefolgert**, 154 abgelehnt obwohl gefolgert, 575 abgelehnt und nicht gefolgert; Resolventen zweier Formelklauseln (108): alle 108 akzeptiert. Zusammen 128 / 0 / 154 / 575. | `test_claim_solidaet_zufallsformeln_n30` |
| **Beweisgröße gegen Konflikte** (Zufalls-3-SAT, je n 20 unerfüllbare Formeln) | Bei n = 30 / 40 / 50 (128 / 170 / 213 Klauseln) im Median 22,5 / 43,0 / 62,5 Konflikte (Spanne 13–35 / 24–70 / 23–112) und **genau eine Protokollzeile je Konflikt in allen 60 Protokollen**; gelernte Literale (Median) 70,0 / 164,0 / 294,5; Prüfschritte (Median) 9.312,5 / 26.481,5 / 51.465,0. Der Prüfer akzeptiert alle 60. | `test_claim_beweisgroesse_zufall_live` |
| **Prüfschritte je Löser-Propagation** | Im Median 39,9 / 48,2 / 56,9 bei n = 30 / 40 / 50 (Spannen 33,0–45,7 / 41,2–53,8 / 51,2–62,9); vorgerechnet n = 60 / 70 / 80: 64,5 / 72,6 / 83,1; in den sechs Medianen wächst die Zahl mit n. | `test_claim_beweisgroesse_zufall_live`, `test_claim_beweisgroesse_schritte_je_propagation_in_den_medianen_wachsend_von_n30_bis_n80` |
| **Vorgerechnet n = 60 / 70 / 80** | 20 Formeln je n, alle akzeptiert; Konflikte im Median 100,5 / 140,5 / 201,5, Prüfschritte (Median) 104.611,5 / 179.726,5 / 331.995,5. Die Datei `bwp_messreihen.json` stimmt mit der Neumessung überein. | `test_claim_beweisgroesse_vorgerechnet_n60_bis_n80_gleicht_der_neumessung` |
| **Neumessung der früheren Reihe** (n = 50, m = 213, Zufalls-Seeds 0 bis 29, SplitMix64) | 10 von 30 Formeln unerfüllbar, alle mit höchstens 120 Konflikten (48 bis 99) und alle akzeptiert; im Median 1,00 Zeilen je Konflikt und 57,7 Prüfschritte je Löser-Propagation. Die Zahlen des Vorversuchs (11 Formeln, 55,6, mit Python-`random`-Formeln) sind damit überholt. | `test_claim_vormessung_n50_m213_seeds_0_bis_29_neu_gemessen` |
| **Schubfach ohne Löschzeilen** (h + 1 Tauben, h Löcher) | Konflikte (gleich Zeilen) 7 / 28 / 159 / 1.004 / 4.811 bei h = 3 / 4 / 5 / 6 / 7, je zusätzliches Loch das 4,0- / 5,7- / 6,3- / 4,8-Fache; Prüfschritte 435 / 4.788 / 64.154 / 1.654.563 / 32.802.504; alle fünf Protokolle akzeptiert (h = 7 **vorgerechnet, nicht live**). | `test_claim_schubfach_ohne_loeschen`, `test_claim_schubfach_faktoren_je_loch_und_loeschzeilen_vergleich`, `test_claim_schubfach_h7_vorgerechnet_in_sich_stimmig_und_loeser_gleicht_der_neumessung` |
| **Schubfach mit Löschzeilen** (der Löser wirft alle 100 Konflikte die schlechtere Hälfte der gelernten Klauseln weg) | Bei h = 3 und 4 keine Löschzeile (7 und 28 Konflikte). Bei h = 5: 167 statt 159 Konflikte, 212 Zeilen davon 45 Löschzeilen, höchstens 203 statt 240 Klauseln gleichzeitig lebend. Bei h = 6: 2.428 statt 1.004 Konflikte, 4.708 Zeilen davon 2.280 Löschzeilen, höchstens 351 statt 1.137 lebende Klauseln, 1.786.925 statt 1.654.563 Prüfschritte. Bei h = 7 (vorgerechnet): 47.374 statt 4.811 Konflikte, 94.529 Zeilen davon 47.155 Löschzeilen, höchstens 454 statt 5.015 lebende Klauseln, 48.482.118 statt 32.802.504 Prüfschritte. Alle Protokolle mit Löschzeilen werden akzeptiert. | `test_claim_schubfach_mit_loeschzeilen_takt_100`, `test_claim_schubfach_h7_vorgerechnet_in_sich_stimmig_und_loeser_gleicht_der_neumessung` |
| **Hinweise statt Suche** (Handbeispiel) | Die Hinweislisten von Hand (zwischen 3 und 5 Klauseln je Zeile) werden akzeptiert; der Hinweisprüfer liest zusammen 19 Klauseln, die Suche des einfachen Prüfers braucht 66 Prüfschritte. Aus der Suche erzeugte Listen (nur die benötigten Klauseln) sind [5, 9, 3], [6, 8, 3], [4, 10, 2], [7, 11, 2], [12, 13, 1]: zusammen 15 gelesene Klauseln. Löschzeile und falscher Hinweis (Klausel 1 statt 4) werden abgelehnt. | `test_claim_handbeispiel_hinweise_19_gelesene_klauseln_gegen_66_pruefschritte`, `test_hinweise_von_hand_aus_dem_handbeispiel_werden_akzeptiert`, `test_hinweise_loeschzeile_und_falscher_hinweis_werden_abgelehnt` |
| **Voreinstellungen** | Kleine Zufallsformel (n = 20): die erste unerfüllbare Formel ab Zufalls-Seed 7000 ist die bei 7001 (85 Klauseln), 22 Konflikte, 22 Zeilen, 5.404 Prüfschritte. Schubfach h = 5: 159 Zeilen, 64.154 Prüfschritte; mit Löschzeilen 212 Zeilen, 167 Konflikte, 64.896 Prüfschritte. | `test_claim_preset_kleine_zufallsformel_und_schubfach_h5` |

**Messungen dieser README, nicht im Test (Scratch-Lauf der Bauphase, nicht im Repo):** (a) 240 Zufallsformeln mit n = 20, 30 und 40 (Zufalls-Seeds 9000 bis 9239), davon 71 laut OR-Tools CP-SAT unerfüllbar: Die Antwort des Lösers stimmt in allen 240 Formeln mit CP-SAT überein, und jedes der 71 Protokolle wird vom Prüfer akzeptiert, mit Löschzeilen (Löschtakt 10) und ohne. (b) 240 Zufallsformeln mit n = 30 und m = 100 (Zufalls-Seeds 4000 bis 4239, alle erfüllbar), je bis zu 60 Kandidaten, Wahrheit durch den Löser: 8.246 Kandidaten, davon 1.163 akzeptiert und gefolgert, **0 akzeptiert und nicht gefolgert**, 1.127 abgelehnt obwohl gefolgert, 5.956 abgelehnt und nicht gefolgert; für 400 der 1.163 akzeptierten Klauseln bestätigt CP-SAT, dass „Formel plus verneinte Klausel“ unerfüllbar ist. Entscheidend ist die Null; die übrigen Zahlen sind mit dem Code im Repo nicht reproduzierbar (Skript und Kandidatenstrom des Scratch-Laufs fehlen: `soliditaet_reihe` mit den Zufalls-Seeds 4000 bis 4239 und dem Standard-Kandidatenstrom liefert 8.214 Kandidaten, davon 1.168 akzeptiert und gefolgert, 0 akzeptiert und nicht gefolgert, 1.082 abgelehnt obwohl gefolgert, 5.964 abgelehnt und nicht gefolgert), die 400 Bestätigungen durch CP-SAT sind nicht nachgerechnet. Im Repo stehen die kleinen Fassungen (`tests/test_oracle_beweise_pruefen.py`).

## Ehrliche Grenzen

- **Das Format ist ein RUP-Protokoll mit Löschzeilen, kein DRAT und kein LRAT.** Verfahren, die neue Variablen einführen oder RAT-Schritte brauchen (Symmetriebrechung mit Hilfsvariablen, Variablenelimination, Variablenaddition), lassen sich damit nicht belegen. DRAT und LRAT stehen nur als Ausblick (Zitate im Reiter), nichts davon ist gebaut oder gemessen.
- **Der Prüfer ist ein unabhängig geschriebenes, einfaches Programm, kein verifizierter Prüfer.** Das Vertrauen beruht auf seiner Kürze, auf der Quelltext-Trennung vom Löser und auf der Solidität an den gemessenen Formeln; es ist kein Beweis seiner Korrektheit. Die Wahrheit „folgt die Klausel?“ kommt für n > 14 vom eigenen Löser, ist also nicht ganz unabhängig; deshalb prüfen die Tests zusätzlich durch Aufzählung (n = 6) und durch OR-Tools CP-SAT.
- **Die Solidität ist an einer Formelfamilie (Zufalls-3-SAT, n = 30, m = 100) mit zwei Kandidatenarten und am Handbeispiel G gemessen.** Für andere Familien, andere Klauselgrößen und Kandidaten aus anderen Quellen sagt die Messung nichts; die Tafel am Handbeispiel (alle 60 Zweierklauseln) ist vollständig, aber klein.
- **Prüfschritte sind ein Maß für die Arbeit, keine Zeit.** Eine Zeile je Konflikt ist die Arbeitsweise dieses Lösers (jede gelernte Klausel, auch eine Einheitsklausel, wird protokolliert), keine Annahme über andere Löser.
- **Die Beweisgröße ist bis n = 80 (Zufall, 20 Formeln je n, ab n = 60 vorgerechnet) und bis h = 7 (Schubfach) gemessen.** Das Wachstum beim Schubfach ist eine eigene Messung an dieser einen Familie, kein Gesetz. Die theoretische Untergrenze für Resolutionsbeweise des Schubfachs stammt von Haken (1985, Theoretical Computer Science 39); hier nur zitiert, die Primärquelle ist nicht gelesen. Beweise im Petabyte-Bereich (Beweis zu Schur Five, Heule, AAAI 2018: rund zwei Petabyte, mit einem formal verifizierten Prüfer zertifiziert) liegen weit außerhalb; die Demo bildet sie nicht nach.
- **Löschtakt 100 ist eine Wahl der Demo.** Der Kern löscht standardmäßig alle 2.000 Konflikte; dann hätte das Schubfach bis h = 6 keine Löschzeile. Mit Löschzeilen sucht der Löser anders (mehr Konflikte); der Vergleich „mit und ohne“ ist deshalb einer zweier Läufe, nicht derselben Suche.
- **Ein akzeptierter Beweis zeigt „unerfüllbar“ nur für die vorliegende Formel.** Wurde sie vorher erweitert (Symmetriebrechung) oder vereinfacht (Vorverarbeitung), gilt er für diese Formel, nicht für die ursprüngliche.
- **Manipulationen an einem Protokoll einer unerfüllbaren Formel** sagen nichts über die Solidität (dort folgt jede Klausel, auch eine falsch geschriebene Zeile ist semantisch wahr); die App zeigt dort nur das Urteil des Prüfers.
- Hinweise: Die Hinweislisten der Demo sind kein LRAT; die Aussagen über LRAT, DRAT, cake_lpr, GRAT, VeriPB/CakePB, Pumpkin (Format DRCP, nicht VeriPB) und Flippo u. a. (CP 2024, nur das Abstract gelesen) sind Zitate des Leseprotokolls, keine eigene Messung.

## Befunde und Korrekturen gegenüber dem Plan

1. **Der einfache Prüfer ist schnell genug für mehr als der Plan annahm.** Der Plan sah live Handbeispiel, n ≤ 30 und Schubfach h ≤ 5 vor und h = 7 nur als Konfliktzahl. Gebaut ist: Zufallsformeln live bis n = 50 (Messreihe auf Knopfdruck), vorgerechnet bis n = 80; Schubfach live bis h = 6 (Messreihe auf Knopfdruck), h = 7 vorgerechnet **mit Prüfer**, mit und ohne Löschzeilen. Die Zahlen des Vorversuchs (n ≤ 50, h ≤ 6 im Selbsttest) sind damit erweitert, nicht widerlegt.
2. **Alle Zahlen des Vorversuchs sind überholt** (andere Formeln: dort Python-`random`, hier SplitMix64): 11 unerfüllbare Formeln und 55,6 Prüfschritte je Propagation bei n = 50 wurden zu 10 Formeln und 57,7; die Solidität 9 / 0 / 132 / 619 und 96 Resolventen zu 20 / 0 / 154 / 575 und 108 (857 statt 856 Kandidaten). Der Befund bleibt: Fehlerzelle 0.
3. **Die Hinweislisten des Plans (Teil C) sind von Hand geordnet** und enthalten bei A und B Klauseln, die der Widerspruch nicht braucht (4 und 7 bei A: [4, 5, 7, 9, 3]; 4 und 7 bei B: [7, 8, 4, 6, 3]); C, D und E nennen dieselben Klauseln in anderer Reihenfolge als die erzeugten Listen. Beide Fassungen (von Hand und erzeugt) werden vom Hinweisprüfer akzeptiert (Reiter „Ausblick“: Auswahl „Hinweise“).
4. **„Vertauschen von A und C wird abgelehnt“ (Plan) gilt nicht:** C = (¬x1) ist schon ohne A aus der Formel herleitbar (x1 erzwingt ¬x3, ¬x5, x4, ¬x6 und verletzt Klausel 3). Abgelehnt wird stattdessen die Reihenfolge A, B, E, C, D: E (die leere Klausel) braucht C und D und steht in Zeile 3 zu früh.
5. **Schnittstellenwünsche an den Kern:** Der Kern bleibt unverändert (Kopie mit Hash-Test). Die Wünsche 1 bis 4 (erklärende Prüfung, Hinweise, Fehlerort, Löschen unbekannter Klauseln) sind in `bwp_pruefer.py` umgesetzt, das dieselben Prüfschritte zählt wie `bwp_rup.py` (Test auf gleiche Zähler an Beweisen des Lösers und an veränderten Protokollen); Wunsch 5 (Einheitsklauseln im Löser) ist über die Klauselnummern des Bestands berücksichtigt (jede Zeile `a (l)` ist eine lebende Klausel); Wunsch 6 sichert ein Quelltext-Test.
6. **Löschzeilen nur beim Schubfach** (nicht bei Zufallsformeln): Bei n ≤ 50 hat in der Messreihe keine Formel mehr als 112 Konflikte, der Regler wäre dort meist ein stiller No-Op.
7. **Beim Handbeispiel zeigt die App wahlweise den Beweis von Hand (A bis E) oder den des Lösers.** Der Löser schreibt nur zwei Zeilen (`a (¬x2)`, `a ()`); beide werden akzeptiert.

## Bewusst nicht umgesetzt

DRAT- und LRAT-Dateien lesen oder schreiben, ein verifizierter Prüfer, Beweise mit Erweiterungsvariablen, CP-Beweise (Pumpkin, DRCP: nur Ausblick-Text), Beweisgrößen im Gigabyte- oder Petabyte-Bereich, Zeitmessungen, Beweise für MaxSAT oder Optimalität, ein Prüfer mit beobachteten Literalen (er würde den Vorteil der Einfachheit aufgeben).

## Verifikation

- **Kern:** Handbeispiel PHP(2) von Hand (fünf Zeilen A bis E, Prüfschritte je Zeile 12 / 13 / 13 / 14 / 14), Kette der Einheiten je Zeile, Fehlerort, Löschzeilen (auch für nie vorhandene Klauseln), Reihenfolge der Zeilen, Tautologien, doppelte Literale, Protokoll ohne leere Klausel, leere Formel, Formel mit leerer Klausel, Einheitsklauseln, n = 1 (`tests/test_pruefer.py`, `tests/test_algorithm.py`, `tests/test_edge_cases.py`); Regressionstests der kopierten Kern-Module (`tests/test_kern_rup.py`, `tests/test_kern_rng_instanzen.py`) und Hash-Test der Kopien (`tests/test_copies.py`).
- **Orakel** (`tests/test_oracle_beweise_pruefen.py`): Solidität des Prüfers gegen eine eigene Aufzählung aller Belegungen (n = 6, jede der 60 Zweierklauseln und jede Resolvente an 80 Formeln), gegen den Löser und OR-Tools CP-SAT an Zufallsformeln mit n = 30, **jede vom Löser als unerfüllbar beantwortete Formel hat ein akzeptiertes Protokoll** (mit und ohne Löschzeilen; Antwort gegen CP-SAT), Zweig-Test mit einem absichtlich fehlerhaften Prüfer (Mutant nur im Test), Hinweisprüfer gegen die Suche. Im Scratch-Lauf mit 240 Formeln siehe oben.
- **Unabhängigkeit des Prüfers:** Quelltextprüfung, dass `bwp_rup.py` und `bwp_pruefer.py` weder `bwp_cdcl.py` noch dessen Namen importieren (`tests/test_pruefer.py`).
- **Verdikte:** reine Funktionen `bwp_evaluation.verdict_*`, jede Zahl im Text an handgesetzten Werten (`tests/test_verdicts.py`); **Claims:** jede Zahl dieser README an festen SplitMix64-Seeds (`tests/test_claims.py`, `BWP_LANGSAM=1` zusätzlich die Neumessung von h = 7).
- **Presets:** vollständig, Werte innerhalb der Reglergrenzen, Standard-Preset gleich Standardeinstellung (`tests/test_presets.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), Footer-Test, Laufzeit-Importe.
- **Layout:** Schnellstart oben in der Seitenleiste, fester Kopf, aktives Preset hervorgehoben; jede Änderung eines Reglers hebt die Markierung auf; nicht wirksame Regler sind gesperrt (`tests/test_layout.py`).

Die Suite hat 155 Tests (`pytest --collect-only -q tests`); einer davon (die Neumessung von Schubfach h = 7 mit Prüfer, einige Minuten) läuft nur mit `BWP_LANGSAM=1` und ist sonst übersprungen. Alle Zählungen sind ganzzahlig und auf jeder Plattform dieselben; die Tests prüfen sie exakt.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `bwp_algorithm.py` | Löser-Anbindung, Wahrheit, Solidität, Manipulation, Messzeilen, Hinweisbeispiel |
| `bwp_pruefer.py` | Prüfer mit Erklärung, Fehlerort, Hinweise (ohne Import aus dem Löser) |
| `bwp_cdcl.py`, `bwp_rup.py`, `bwp_rng.py`, `bwp_instanzen.py` | wörtliche Kopien aus dem Kern-Paket der Linie |
| `bwp_constants.py` | Regler-Grenzen, feste Annahmen, Handbeispiel, Farben, Presets |
| `bwp_evaluation.py` | Verdikte, Tabellen, vorgerechnete Zeilen |
| `bwp_layout.py` | Fester Kopf (Stylesheet) |
| `bwp_messreihen.json` | vorgerechnete Zeilen (Schubfach h = 7, Zufall n = 60 bis 80), erzeugt mit `tools/messreihen.py` |
| `bwp_presets.py` | Permalink (Begrenzen), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `bwp_scenario.py` | Formeln, Schreibweise, Klauseleingabe |
| `bwp_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tools/kern_kopieren.py` | kopiert die Kern-Module und schreibt die Kopfzeilen |
| `tools/messreihen.py` | erzeugt `bwp_messreihen.json` |
| `requirements-dev.txt` | Laufzeit plus pytest und OR-Tools (nur Gegenprobe im Test) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Handbeispiel, Prüfer, Orakel, Claims, Verdikte, Randfälle, Kern-Regression, Presets, Layout, AppTest-Smoke-Test, Footer, Laufzeit-Importe |

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und pandas; OR-Tools nur in den Tests.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [SAT und CP: Konfliktlernen bis Wahl](https://sebastianhanisch.net/konzepte-sat-constraint-programming.html).
