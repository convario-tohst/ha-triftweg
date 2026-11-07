#!/usr/bin/env python3
"""oxxify / Blauberg-Vento-Lüfter (Sauna) lokal per UDP 4000 steuern.
  oxxify.py status                 → JSON (an, stufe, drehzahl_manuell, modus, feuchte, rpm1, rpm2, ...)
  oxxify.py an | aus
  oxxify.py stufe 1|2|3            → feste Stufe
  oxxify.py prozent 0..100         → manuelle Drehzahl (Stufe 255)
  oxxify.py modus 0|1|2            → 0 Lüftung (Abluft), 1 Wärmerückgewinnung, 2 Zuluft
"""
import json, socket, sys

IP, DEV, PW = "192.168.11.144", b"0034001E42435718", b"1111"


def paket(func, data):
    body = bytes([0x02, len(DEV)]) + DEV + bytes([len(PW)]) + PW + bytes([func]) + data
    return b"\xFD\xFD" + body + (sum(body) & 0xFFFF).to_bytes(2, "little")


def senden(func, data, antwort=True):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(2)
    for _ in range(3):  # UDP: bis zu 3 Versuche
        s.sendto(paket(func, data), (IP, 4000))
        if not antwort:
            return None
        try:
            return s.recvfrom(2048)[0]
        except socket.timeout:
            continue
    raise SystemExit("keine Antwort")


def lesen(params):
    d = senden(0x01, bytes(params))
    p = 2 + 1 + 1 + d[3] + 1 + d[4 + d[3]] + 1
    w = {}
    while p < len(d) - 2:
        b = d[p]
        if b == 0xFE:
            ln, par = d[p + 1], d[p + 2]; w[par] = int.from_bytes(d[p + 3:p + 3 + ln], "little"); p += 3 + ln
        elif b == 0xFD:
            p += 2
        elif b == 0xFF:
            p += 2
        else:
            w[b] = d[p + 1]; p += 2
    return w


def schreiben(par, wert):
    senden(0x03, bytes([par, wert]))  # 0x03 = schreiben mit Antwort


cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
if cmd == "an":
    schreiben(0x01, 1)
elif cmd == "aus":
    schreiben(0x01, 0)
elif cmd == "stufe":
    schreiben(0x02, max(1, min(3, int(sys.argv[2]))))
elif cmd == "prozent":
    schreiben(0x02, 255)
    schreiben(0x44, max(0, min(100, int(float(sys.argv[2])))))
elif cmd == "modus":
    schreiben(0xB7, max(0, min(2, int(sys.argv[2]))))
w = lesen([0x01, 0x02, 0x44, 0xB7, 0x25, 0x19, 0x0F, 0x4A, 0x4B, 0x83, 0x06])
print(json.dumps({
    "an": w.get(0x01) == 1, "stufe": w.get(0x02), "drehzahl_manuell": w.get(0x44),
    "modus": {0: "Lüftung", 1: "Wärmerückgewinnung", 2: "Zuluft"}.get(w.get(0xB7), w.get(0xB7)),
    "modus_nr": w.get(0xB7), "feuchte": w.get(0x25), "feuchte_schwelle": w.get(0x19),
    "feuchtesensor_aktiv": w.get(0x0F) == 1, "rpm1": w.get(0x4A), "rpm2": w.get(0x4B),
    "alarm": w.get(0x83), "boost": w.get(0x06) == 1}))
