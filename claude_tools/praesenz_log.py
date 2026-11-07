"""Hängt eine Zeile an das Präsenz-Protokoll an: /config/protokoll/praesenz_JJJJ-MM.csv
Usage: praesenz_log.py <raum> <an|aus> [dauer_sekunden]"""
import os, sys, datetime

raum, zustand = sys.argv[1], sys.argv[2]
dauer = sys.argv[3] if len(sys.argv) > 3 else ""
jetzt = datetime.datetime.now()
ordner = "/config/protokoll"
os.makedirs(ordner, exist_ok=True)
datei = os.path.join(ordner, f"praesenz_{jetzt:%Y-%m}.csv")
neu = not os.path.exists(datei)
with open(datei, "a", encoding="utf-8") as f:
    if neu:
        f.write("datum;uhrzeit;wochentag;raum;zustand;dauer_min\n")
    min_ = f"{float(dauer) / 60:.1f}" if dauer.replace(".", "", 1).isdigit() else ""
    f.write(f"{jetzt:%Y-%m-%d};{jetzt:%H:%M:%S};{jetzt:%a};{raum};{zustand};{min_}\n")
