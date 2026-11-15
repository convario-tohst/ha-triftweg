# Home Assistant Triftweg – Änderungsprotokoll

## 15.11.2026
- Musik: „Läuft gerade“, Musik-Karten und Sprachantworten erkennen auch Wiedergabe direkt am Lautsprecher (LinkPlay-App/Sender), nicht nur Music Assistant (packages/musik_quelle.yaml, Dashboard Start + Musik)
- Frostwarnung: Fehler behoben – Automation nutzte falschen Sensornamen (`sensor.tiefstwert_aussen_48h` statt `_48_h`), Push wäre nie gekommen; Zeitangaben robust gegen fehlende Werte
- Projektunterlagen + CLAUDE.md ins Repo übernommen (für Arbeit mit Claude Code im persönlichen Konto)

## 12.11.2026
**Bad Yvonne: HA schaltet Licht nach Präsenz** (packages/bad_yvonne_licht.yaml)
- ETS: Melder 1.1.32 Objekt 0 (Lichtgruppe 1 Schalten) von 0/0/10 auf neue GA 0/7/10 „Licht Präsenz Bad Yvonne“ umgehängt, helligkeitsunabhängig, Nachlauf 5 min
- HA: Schema wie HWR/Ankleide Tobias – an bei Präsenz + < 300 lx, tagsüber 80 %, Nachtzeit EG 20 %, aus 1 min nach Präsenz-Ende; manuell aus bleibt aus bis Raum leer
- Extra: Schalter „Bad Yvonne: Entspannen“ (Wanne) – Licht bleibt gedimmt 25 % an, endet nach 2 h
- Raumansicht Bad Yvonne: Block „Wohlfühlen“; Automatik-Ansicht: Einstellwerte Bad Yvonne
- Glastaster 1.1.14 T1/2 Decke dimmen: Obj 0 → 0/0/10, Obj 1 → 0/1/14, Obj 3 → 0/2/17

## 08.11.2026
- Bad Yvonne LED-Leiste: zufällige ruhige Effekte/romantische Paletten, Wechsel alle 10 min (packages/bad_yvonne_stimmung.yaml)
- Frostwarnung: 48-h-Vorhersage, Push an Tobias + Yvonne ab ≤ 1 °C, Erinnerung 18 Uhr (packages/frost.yaml)
- Designs „Triftweg“ (warm) / „Triftweg Frost“ (eisblau), automatische Umschaltung (themes/triftweg.yaml)
- Dashboard: Klima-Bereich einklappbar (Kopfzeile: Temperatur außen, Feuchte innen, Frost-Hinweis), klappt nach 3 min zu (packages/dashboard_klima.yaml)
- KNX-Projekt exportiert nach knx/Triftweg.knxproj

## 07.11.2026 (abends)
- Nachtlicht Flur Malte → HA (packages/nachtlicht.yaml): an unter 50 lx außen, aus über 100 lx, aus bei Abwesenheit. Ursache vorher: Timberwolf (Objekt 303) schaltete 0/0/3 wieder ein
- Flur EG bei Heimkehr: gewolltes Begrüßungslicht (Rückkehr per Handy, bei Dunkelheit)
- Integration „Model Context Protocol Server“ eingerichtet; Connector-URL: Nabu-Casa-Adresse + /api/mcp

## 07.11.2026
**Sicherung**
- Git-Sicherung: privates Repo convario-tohst/ha-triftweg (Deploy-Key auf dem HA), nachts 03:30 + Skript „Konfiguration sichern (GitHub)“
- Ausgeschlossen: secrets.yaml, Tokens/.storage (bis auf Dashboards/Bereiche/Listen), Datenbank, Logs, Präsenz-Protokolle

**Lüftung / Entfeuchter** (Analyse 28.10.–07.11.: Lüftung Ø 60 %, 26 % der Zeit Boost 100 %, Modus „trocknen“ 94 %)
- Bad-Boost nur noch beim Verlassen, nur nach ≥ 2 min Benutzung, nicht bei Abwesenheit, Dauer 10 min
- Ankleide zählt nicht mehr für die Hausregelung und den Taupunkt innen; Feuchtewarnung bleibt
- Entfeuchter: Wenn die Lüftung trocknet, erst ab Ziel + 8 % an, unter Ziel + 3 % aus (sonst Ziel + 2 / Ziel − 2)
- Stufen: Trocknen 45 %, nachts 35 %; bei Außenluft < 5 °C max. 40 %
- Hängende 1-Wire-Werte werden erkannt (Sensor „HA Startzeit“)

**Anwesenheit**
- „Abwesend nach 15 min ohne Bewegung“ (7–22 Uhr, nicht bei TV/Musik, Sauna, Disco, Sauger)
- Rückkehr über alle Innen-Präsenzmelder + Ring innen
- „Haus verlassen“: Giebellicht bleibt an

## Offen
- Präsenz-GAs für weitere Melder: Ankleide Yvonne 1.1.27 → 0/7/11, Bad OG 1.1.18 → 0/7/12, Flur EG 1.1.22 → 0/7/13, Sauna Bad 1.1.39 → 0/7/14
- Timberwolf: Funktion an Objekt 303 (Nachtlicht 0/0/3) finden und deaktivieren
- Präsenzmelder Flur OG 1.1.24: Präsenzempfindlichkeit 8 → 5 (Lichtkanal 1+2), Bewegungsfilter; später 0/1/6 trennen und HA schaltet
- Vallox-Filter überfällig → wechseln, Datum zurücksetzen
- 1-Wire OG (Schlafzimmer, Malte, Lara) liefert seit Tagen keine Werte → Strang am Timberwolf prüfen
- Raspberry Pi meldet Unterspannung → Netzteil tauschen
- Lichter „Einfahrt Leuchte“ und „Mülltonne Leuchte“ nicht erreichbar
- Roborock: Verbindungsfehler
- Mammotion: zweites Konto anlegen, Integration neu einrichten
- Fernzugriff: Connector in claude.ai hinzufügen
