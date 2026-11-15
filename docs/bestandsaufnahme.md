# Home Assistant Triftweg – Bestandsaufnahme (Stand 07.11.2026)

## System
- Home Assistant OS auf Raspberry Pi (Unterspannung gemeldet!), `http://192.168.11.18:8123`
- Konfigurationszugriff: Samba-Add-on → Windows-Laufwerk H:\ (= /config), Git-Repo convario-tohst/ha-triftweg
- Struktur: configuration.yaml → packages/ (Themen-Dateien), knx.yaml, automations.yaml (UI-Automationen)
- Hilfswerkzeuge: claude_tools/ (systemtest.py, gelernt.py, liste_anlegen.py, oxxify.py, praesenz_log.py, ha_git_backup.sh)
- Backups vor Änderungen: claude_backup/<datum>/
- Präsenz-Protokolle: protokoll/praesenz_JJJJ-MM.csv (nicht im Git)

## Architektur Hausautomation
- KNX (Integration „knx“, knx.yaml): Lichter, Heizkreise, Rollläden, Präsenzmelder, Sensoren, Szenen, Schalter
- KNX-IP: Timberwolf Server 1.1.10, 192.168.11.5
- DALI: MDT DALI Control IP 1.1.4 (Gruppen als KNX-GA 0/0/x, Dimmen 0/1/x, Status 0/2/x)
- 1-Wire: Timberwolf → KNX (Temperatur, Feuchte 4/0/N, Helligkeit 4/1/N, Taupunkt 4/2/N, abs. Feuchte 4/3/N)
- Weitere: Ring, Vallox (Lüftung), Midea (Entfeuchter), Roborock, Music Assistant + LinkPlay/DLNA, WLED, UniFi, Fritz, Samsung TV, Voice PE (ESPHome), Anthropic (Sprachassistent), Müllkalender AWB Oldenburg
- Bereiche: EG, OG, Außen; 17 Räume

## Packages (Themen, Auswahl)
Anwesenheit/Präsenz, Außenlicht, Einfahrt, Licht EG/HWR/Nacht/Ankleide Tobias, Bad Yvonne (Licht, Stimmung), Nachtlicht, Flur-OG-Sicherheitsnetz, Melder sperren, Wohnzimmer-Präsenz, Kinder wach, Sauna + Sauna-Lüftung, Lüftung, Raumfeuchte, Raumklima-Nutzung, Entfeuchter, Komfort, Frost, Dashboard-Klima, Musik (KI, Listen, Quelle, Suche, Blacklist), Lautstärke-Fade, Sprache, Voice PE, Müll, Urlaub, Ring, Klingel-Blinken, Staubsauger, Listen/Einkauf, Erinnerungen, WhatsApp, Ballonwetter, Netzwerk, System-Wächter, Systemtest, Git-Backup, Zeitsteuerung, Haus

## Offene Änderungswünsche (HA-Liste „Änderungswünsche“, Auszug 07.11.)
- Zweiter Raspberry Pi als Backup
- Steckdosen Wohnzimmer schalten immer noch
- Ballonfahrtwetter-Ampel funktioniert nicht
- Musik: Fade-in/out, Startlautstärke, fehlgeschlagene Sprachbefehle
- Wohnzimmer-Audio: Voice PE per Klinke anbinden
- Durchsage „Kinder oben rufen“, Schnell-Button „Mittagsschlaf“
- WhatsApp-Versand per Sprache
- Müll-Erinnerung Küchenstripe
- Carport-Licht bei Ankunft
- Startwort „Ludwig“ trainieren
- Ring: veraltete Bewegungs-Entitäten in ~15 Automationen auf Event-Entitäten umstellen
