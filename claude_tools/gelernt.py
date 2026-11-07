#!/usr/bin/env python3
"""Erzeugt custom_sentences/de/gelernt.yaml aus der Liste "Gelernte Sprachbefehle".

Jeder Eintrag: SUMMARY = gesprochener Satz (normalisiert), DESCRIPTION = JSON
  {"dienst": "light.turn_on", "ziel": ["light.x"], "daten": {}, "antwort": "…", "anzahl": 2}
Lokal aktiv werden nur Einträge mit anzahl >= MIN (wiederholt benutzt) und Status "offen".
Zusätzlich enthält die Datei den Auffangsatz "AnClaude" (alles Unklare geht an Claude).
Aufruf: shell_command (läuft im HA-Container), danach conversation.reload.
"""
import json, re

ICS = "/config/.storage/local_todo.gelernte_sprachbefehle.ics"
OUT = "/config/custom_sentences/de/gelernt.yaml"
MIN = 2
ERLAUBT = ("light.", "switch.", "scene.", "cover.", "media_player.", "script.musik", "script.ring", "fan.",
           "input_boolean.", "climate.set_temperature", "input_select.")


def unfold(text):
    return re.sub(r"\r?\n[ \t]", "", text)


def unesc(v):
    return (v.replace("\\n", "\n").replace("\\N", "\n").replace("\\,", ",")
             .replace("\\;", ";").replace("\\\\", "\\"))


def todos():
    try:
        raw = unfold(open(ICS, encoding="utf-8").read())
    except FileNotFoundError:
        return []
    out, cur = [], None
    for line in raw.splitlines():
        if line == "BEGIN:VTODO":
            cur = {}
        elif line == "END:VTODO":
            out.append(cur)
            cur = None
        elif cur is not None and ":" in line:
            k, v = line.split(":", 1)
            cur[k.split(";")[0]] = unesc(v)
    return out


def norm(s):
    s = s.lower().strip()
    s = re.sub(r"[^\wäöüß %]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


saetze = []
for t in todos():
    if t.get("STATUS", "").upper() != "NEEDS-ACTION":
        continue
    try:
        d = json.loads(t.get("DESCRIPTION", "{}"))
    except ValueError:
        continue
    satz = norm(t.get("SUMMARY", ""))
    dienst = str(d.get("dienst", ""))
    ziel = d.get("ziel") or []
    ziel = [ziel] if isinstance(ziel, str) else list(ziel)
    if not satz or int(d.get("anzahl", 1)) < MIN:
        continue
    if not (dienst.startswith(ERLAUBT) or all(z.startswith(ERLAUBT) for z in ziel)) or "saunaofen" in json.dumps(d):
        continue
    saetze.append((satz, dienst, ziel, d.get("daten") or {}, d.get("antwort") or "Erledigt."))

lines = [
    "language: de",
    "# AUTOMATISCH ERZEUGT von /config/claude_tools/gelernt.py – nicht von Hand bearbeiten",
    "intents:",
    "  AnClaude:",
    "    data:",
    "      - sentences:",
    '          - "{satz}"',
]
if saetze:
    lines += ["  GelernterBefehl:", "    data:"]
    for satz, dienst, ziel, daten, antwort in saetze:
        lines += [
            "      - sentences:",
            "          - " + json.dumps(satz, ensure_ascii=False),
            "        slots:",
            "          dienst: " + json.dumps(dienst),
            "          ziel: " + json.dumps(json.dumps(ziel)),
            "          daten: " + json.dumps(json.dumps(daten, ensure_ascii=False), ensure_ascii=False),
            "          antwort: " + json.dumps(antwort, ensure_ascii=False),
        ]
lines += ["lists:", "  satz:", "    wildcard: true", ""]
open(OUT, "w", encoding="utf-8").write("\n".join(lines))
print(f"{len(saetze)} gelernte Kurzbefehle aktiv")
