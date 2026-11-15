# Home Assistant Triftweg – Arbeitsanleitung für Claude

Dieses Repo ist der `/config`-Ordner des Home Assistant von Tobias Ohst (Triftweg 106, Oldenburg).
Es wird jede Nacht 03:30 automatisch vom HA nach GitHub gesichert (`packages/git_backup.yaml`).
Projektunterlagen: `docs/bestandsaufnahme.md`, `docs/aenderungen.md` (Änderungsprotokoll – bei jeder Änderung ergänzen).

## System
- HA OS auf Raspberry Pi, `http://192.168.11.18:8123`, extern über Nabu Casa
- KNX über Timberwolf Server 1.1.10 (`192.168.11.5`, KNXnet/IP), DALI über MDT DALI Control IP 1.1.4,
  1-Wire über Timberwolf → KNX (4/0/N Feuchte, 4/1/N Helligkeit, 4/2/N Taupunkt, 4/3/N abs. Feuchte)
- ETS-Projekt: `knx/Triftweg.knxproj` (Export, mit xknxproject auswertbar)
- Präsenz-Gruppenadressen 0/7/x (Melder melden nur Präsenz, HA schaltet das Licht): 0/7/0 Malte, 0/7/1 Lara,
  0/7/2 Schlafzimmer, 0/7/3 Gästebad, 0/7/4 Flur OG, 0/7/5 Außensauna, 0/7/6 Wohnzimmer, 0/7/8 HWR,
  0/7/9 Ankleide Tobias, 0/7/10 Bad Yvonne; geplant 0/7/11 Ankleide Yvonne, 0/7/12 Bad OG, 0/7/13 Flur EG, 0/7/14 Sauna Bad

## Zugriff (Claude Code auf Tobias' Windows-PC)
- Arbeitsordner = `H:\` (Samba-Freigabe von `/config`), das ist zugleich das Git-Repo.
- **Nicht selbst auf H:\ committen/pushen** – Git-Sicherung macht der HA (nachts + `shell_command.git_backup`),
  sonst kollidieren zwei Git-Clients auf demselben `.git`.
- HA-API: `http://192.168.11.18:8123/api/…` mit Token aus Umgebungsvariable `HA_TOKEN`
  (Header `Authorization: Bearer $HA_TOKEN`). Token nie ausgeben oder in Dateien schreiben.
  - Prüfen: `POST /api/config/core/check_config`
  - Neu laden: `POST /api/services/<domain>/reload` (input_boolean, input_number, template, script, automation, knx)
  - Sichern: `POST /api/services/shell_command/git_backup` mit `{"nachricht": "…"}`

## Arbeitsweise
- Logik gehört in `packages/<thema>.yaml` (ein Thema pro Datei), KNX-Entitäten in `knx.yaml`.
- Vor Änderungen: Kopie nach `claude_backup/<datum>/` und Git-Sicherung (`shell_command.git_backup` mit Nachricht).
- Nach Änderungen: Konfiguration prüfen (`POST /api/config/core/check_config`), dann gezielt neu laden
  (input_*, template, script, automation, knx) – kein Neustart nötig, außer bei neuen Integrationen.
- Präsenz-Licht-Schema (HWR, Ankleide Tobias, Bad Yvonne): Präsenz an + Lux unter Schwelle → an mit Tag-/Nacht-Helligkeit
  (Nachtzeiten `input_datetime.nacht_eg_*` / `nacht_og_*`), aus nach Nachlauf; manuell aus bleibt aus bis Raum leer;
  Schalter „<Raum>: Licht nach Präsenz“ + Einstellwerte in der Automatik-Ansicht.
- Hängende 1-Wire-Werte zählen nur, wenn nach HA-Start (+10 min) und in den letzten 12 h geändert (`sensor.ha_startzeit`).
- Systemtest: `claude_tools/systemtest.py`, Ergebnis `claude_tools/systemtest_letzter.json` (täglich 05:30).
- Nichts aus `secrets.yaml`, `.ssh/`, `.storage/auth*` lesen oder ausgeben.
- Tobias kommuniziert auf Deutsch, möchte kurze, direkte Antworten. In gebauten Seiten/Apps braucht jeder Knopf einen Tooltip.
