# Home Assistant Triftweg – Änderungsprotokoll

## 24.11.2026
- Abwesenheit: Musik/TV verhindern „Abwesend ohne Bewegung“ nur noch bis 45 min ohne Bewegung (morgens lief die Morgenmusik weiter, Haus galt als bewohnt, Lichter blieben an)
- Haus verlassen: tagsüber gehen alle Lichter aus, auch draußen und der Giebel (Giebel bleibt nur abends an); Gruppe „Alle Lichter“ um Außensauna-Leiste, Mülltonne, Einfahrt ergänzt
- Wohnzimmer Morgenlicht (packages/wohnzimmer_praesenz.yaml): bei Präsenz 04:30–10 Uhr (wenn dunkel und noch kein Licht an) statt Szene Relax: Küche 31 %, Esstisch 35 %, Sofa 20 %, Küchen-Stripe 70 % – vor 6 Uhr ×0,7, bei Dämmerung außen (5–100 lx) ×0,8, darüber ×0,6; Stripe nicht bei Müll-/Frost-Blinken; Schalter „Morgenlicht“ auf der Raumseite Wohnen & Küche

## 23.11.2026
- Frost: Küchen-Stripe blinkt schnell weiß am Tag vor dem Frost und am Frosttag, 6–22 Uhr (packages/frost_stripe.yaml); abstellbar mit „Frost-Blinken aus“ (gilt bis Frostwarnung vorbei) oder ganz mit „Frost: Küchen-Stripe blinkt“; Müll-Erinnerung hat Vorrang
- Schnee heute/morgen in der Vorhersage: statt Blinken weißes Glitzern auf Eisblau (WLED „Sparkle“), Sensor `binary_sensor.schnee_heute_oder_morgen`

## 22.11.2026
**Präsenzmelder sperren auf jeder Raumseite** (packages/melder_raumsperre.yaml)
- Schalter „Präsenzmelder sperren“ oben auf jeder Raumseite; gesperrt = Melder schaltet kein Licht, alle Sperren heben sich um 5 Uhr auf
- HA-Räume (HWR, Ankleide Tobias, Bad Yvonne, Sauna innen): Sperre als Bedingung in der Licht-Automation
- Malte, Lara, Schlafzimmer: Sperre schaltet die Präsenz-Automation aus, Entsperren nur innerhalb der Wachzeit wieder an; Zeitplan respektiert die Sperre
- KNX-Sperrobjekte (1 Bit, 1 = gesperrt): Flur EG 0/5/1 (bisher fälschlich als 2-Bit-Select angelegt → jetzt Schalter), neu Bad OG 0/5/3, Gästebad 0/5/6, Ankleide Yvonne 0/5/7, Flur OG 0/5/8, Werkstatt 0/5/9, Sauna Bad 0/5/10 – **in der ETS noch verknüpfen**
- Garten & Einfahrt: bestehende Auswahl „Melder Sauna außen“ (Automatik / Aus / An)

## 21.11.2026
**Fehlerbereinigung (Systemprotokoll)**
- Müll-Durchsage Wohnzimmer: Skript brach seit 20.11. ab (`response_variable` bei play_announcement) → behoben; Rückfall ohne Music Assistant direkt auf media_player.wohnzimmer
- Heizung Ankleide: Betriebsart-Status 3/4/2 wird nicht mehr gelesen (antwortet nicht, 46.000 Warnungen)
- Sauna-Lüftung (oxxify.py): 5 statt 3 UDP-Versuche (vorher ~3 Aussetzer/Tag)
- Ring: Anmeldung abgelaufen (seit ~09.11. alle Kamera-Entitäten nicht verfügbar) → Neuanmeldung durch Tobias nötig
- Musik „nicht gefunden“: Music Assistant hat nur TuneIn (Radio) – Künstler/Titel brauchen einen Musikdienst (SoundCloud geplant)
- Nachtlicht Flur OG: Schalter „Nachtlicht Flur: heute Nacht aus“ (Licht sofort aus und bleibt aus, auch wenn KNX es wieder einschaltet; 10 Uhr automatisch zurück) + „automatisch“ auf der Startseite (Schnell)
- Dashboard „Wohnen & Küche“: toter Regler „Präsenzmelder“ (alte Select-Entität) entfernt, Entität gelöscht
- Voice PE Wohnzimmer: neues Startwort „Hey Ludwig“ (microWakeWord, auf Colab mit deutschen Piper-Stimmen trainiert; www/ludwig/hey_ludwig.json + .tflite, Schwelle 0,8). Aktivierungswort 1 = Okay Nabu, 2 = Hey Ludwig
- Erkennung zu schwach → Schwelle 0,6; neue Entität `number.wohnzimmer_voice_wohnzimmer_hey_ludwig_schwelle` (0,3–0,99) stellt die Schwelle ohne Neukompilieren ein
- Test 18:45–18:55: Modell trennt nicht (eigene Stimme Ø 0,3–0,45, Fehlauslösungen durch Geräusche ähnlich) → „Hey Ludwig“ wieder abgeschaltet (Aktivierungswort 2 = aus). Offen: Nachtraining mit echten Sprachaufnahmen
- Firmware-Paket fest auf Voice-PE-Release 26.9.0 (Hauptzweig braucht neueres ESPHome als 2026.10)

## 15.11.2026
- Musik: „Läuft gerade“, Musik-Karten und Sprachantworten erkennen auch Wiedergabe direkt am Lautsprecher (LinkPlay-App/Sender), nicht nur Music Assistant (packages/musik_quelle.yaml, Dashboard Start + Musik)
- Frostwarnung: Fehler behoben – Automation nutzte falschen Sensornamen (`sensor.tiefstwert_aussen_48h` statt `_48_h`), Push wäre nie gekommen; Zeitangaben robust gegen fehlende Werte
- Projektunterlagen + CLAUDE.md ins Repo übernommen (für Arbeit mit Claude Code im persönlichen Konto)
- Melder Wohnzimmer sperren: Schalter „Melder Wohnzimmer gesperrt“ (Startseite Schnell, Wohnen & Küche, Automatik, Sprache). HA-Licht reagiert nicht auf Präsenz; KNX 0/5/5 (1 Bit) → Melder 1.1.23 Lichtkanal 1 **Objekt 8 „Sperre“** (Sperrobjekt, aktuellen Zustand verriegeln), LED rot bei Sperre ohne Präsenz / grün mit Präsenz. Hebt sich nach 3 h bzw. um 5 Uhr auf; Taster-Sperre wird übernommen. Alte 2-Bit-Auswahl „Melder Wohnzimmer“ entfernt.
- Automatik-Seite: Präsenzmelder nach Räumen gegliedert (EG/OG/Sauna), Zeiten bei den Zimmern, fehlende Einträge behoben
- Hinweis Übertragung: Wiederholtes Überschreiben derselben Datei über die PC-Brücke kam teils nicht an (Bad Yvonne, Frost, CLAUDE.md) – nachgereicht und per Dateivergleich geprüft

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
