#!/usr/bin/env python3
"""Legt eine neue lokale To-do-Liste in Home Assistant an (läuft per shell_command im HA-Container).
Nutzt den Supervisor-Token des Containers für die HA-API. Usage: liste_anlegen.py "<Name>" """
import json, os, re, sys, urllib.request

name = re.sub(r"[^\w äöüÄÖÜß\-]", "", " ".join(sys.argv[1:])).strip()[:40]
if len(name) < 2:
    print("Name fehlt"); sys.exit(1)
# eigener langlebiger Zugangsschlüssel aus secrets.yaml (Eintrag ha_listen_token)
tok = None
for line in open("/config/secrets.yaml", encoding="utf-8"):
    if line.strip().startswith("ha_listen_token:"):
        tok = line.split(":", 1)[1].strip().strip('"').strip("'")
if not tok or tok == "HIER_EINTRAGEN":
    print("kein Token"); sys.exit(2)
B = "http://127.0.0.1:8123/api/"


def call(path, body=None):
    req = urllib.request.Request(B + path, data=json.dumps(body).encode() if body is not None else None,
                                 method="POST" if body is not None else "GET",
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read() or b"null")


vorhanden = [e["title"].lower() for e in call("config/config_entries/entry") if e["domain"] == "local_todo"]
if name.lower() in vorhanden:
    print("existiert"); sys.exit(0)
f = call("config/config_entries/flow", {"handler": "local_todo"})
r = call(f"config/config_entries/flow/{f['flow_id']}", {"todo_list_name": name})
print(r.get("type"), r.get("title"))
