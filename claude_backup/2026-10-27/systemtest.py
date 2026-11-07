"""Systemtest Triftweg – läuft IN Home Assistant (shell_command.systemtest), schaltet NICHTS.
Nur lesend: Zustände, Konfiguration, Automations-Protokolle (Traces), Log, KNX-Leseanfragen an Präsenzmelder.
Ergebnis: sensor.systemtest (Dashboard „Systemtest“). Aufruf: python3 systemtest.py [sprache]
Priorität: 1 = Präsenz & Licht (kritisch), 2 = Heizung/Klima/System, 3 = Komfort."""
import asyncio, datetime as dt, json, os, re, sys, time
import aiohttp

HIER = os.path.dirname(os.path.abspath(__file__))
TOKEN = open(os.path.join(HIER, ".systemtest_token"), encoding="utf-8").read().strip()
BASIS = "http://127.0.0.1:8123"
H = {"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"}
SPRACHE = "sprache" in sys.argv

# Bekannte Altlasten (verwaist), dürfen "nicht verfügbar" sein
ALTLASTEN = {"light.dimmer_kuche_decke", "light.licht_malte_stripe", "light.licht_gastebad", "climate.wohnzimmer",
             "climate.heizung_obergeschoss", "climate.heizung_bad_yvonne", "climate.heizung_obergeschoss_2"}
# Bekannte Ausfälle: werden als Warnung statt Fehler gemeldet (Text = Grund)
BEKANNT = {r: "1-Wire OG offline" for r in ("_malte", "_lara", "_schlafzimmer")}  # Endung der Entität -> Grund
# Automationen, die selten auslösen dürfen (kein "lief zuletzt"-Hinweis)
SELTEN = {"automation.anwesenheit_ruckkehr_erkannt"}
EREIGNISSE = {f"timer.{x}" for x in ("started", "finished", "cancelled", "paused", "restarted")}
PRAESENZ_RE = re.compile(r"(prasenz|praesenz|presence|bewegung|motion|occupancy)")
PFLICHT = {  # Entität: (Priorität, Kategorie)
    "binary_sensor.jemand_im_haus": (1, "Präsenz & Licht"), "switch.tag_nacht_eg": (1, "Präsenz & Licht"),
    "switch.tag_nacht_og": (1, "Präsenz & Licht"), "select.melder_sauna_aussen": (1, "Präsenz & Licht"),
    "binary_sensor.prasenz_wohnbereich": (1, "Präsenz & Licht"),
    "fan.vallox": (2, "Heizung & Klima"), "humidifier.entfeuchter_og": (2, "Heizung & Klima"),
    "sensor.entfeuchter_og_soll": (2, "Heizung & Klima"), "fan.sauna_luftung": (2, "Heizung & Klima"),
    "sensor.taupunkt_innen": (2, "Heizung & Klima"), "sensor.taupunkt_aussen": (2, "Heizung & Klima"),
    "sensor.luftung_feuchte_modus": (2, "Heizung & Klima"), "sensor.temperatur_wohnzimmer": (2, "Heizung & Klima"),
    "input_boolean.schlafmodus_og": (2, "Heizung & Klima"), "input_boolean.kinder_wach_alarm": (2, "Sicherheit"),
    "media_player.ma_wohnzimmer": (3, "Komfort"), "media_player.ma_schlafzimmer": (3, "Komfort"),
    "assist_satellite.home_assistant_voice_0adb1a_assist_satellit": (3, "Komfort"),
    "conversation.claude_conversation": (3, "Komfort"), "sensor.sprache_zustand": (3, "Komfort"),
    "vacuum.roborock_s7_triftweg": (3, "Komfort"), "todo.musik_lieblingslieder": (3, "Komfort"),
    "input_text.musik_quelle_wohnzimmer": (3, "Komfort"), "sensor.vallox_filter_resttage": (2, "Heizung & Klima"),
    "input_boolean.flur_og_sicherheitsnetz": (1, "Präsenz & Licht"), "binary_sensor.sauger_unterwegs": (1, "Präsenz & Licht"), "sensor.musik_quelle_text": (3, "Komfort"), "sensor.netz_download": (3, "Komfort"),
}
DIENSTE = ["rest_command.wled_aussensauna_alarm", "rest_command.wled_kueche_blinken", "script.sauger_raeume",
           "script.musik_wunsch_abspielen", "script.lautstaerke_faden", "script.musik_aktuell_speichern", "script.musik_gefaellt_mir", "script.musik_lieblingslieder_spielen", "script.liste_anlegen", "script.ich_gehe_ins_bett", "script.alles_aus", "script.system_melden",
           "shell_command.praesenz_log", "shell_command.oxxify", "roborock.get_maps", "vallox.set_profile"]
INTEG_PRIO = {"knx": 1, "vallox": 2, "midea_auto_cloud": 2, "template": 2, "mobile_app": 2, "backup": 2}
# Satzerkennung (nur Testmodus, nichts wird ausgeführt): Satz -> erwartete Absicht
SATZTESTS = [("Mach das Gartenlicht an", "LichtSchnell"), ("Mach das Carport Licht an", "LichtSchnell"),
             ("Schalte das Werkstattlicht aus", "LichtSchnell"), ("Flurlicht oben auf 30 Prozent", "LichtHelligkeit"),
             ("Mach den Küchenstripe an", "LichtSchnell"), ("Wann geht das Gartenlicht aus", "FrageAnClaude"),
             ("Mach im Küchenstripe einen Regenbogen", "EffektSchnell"),
             ("Stell den Flurstripe auf Herzschlag", "EffektSchnell"), ("Mach in Maltes Zimmer die Jalousien hoch", "RolloSchnell"),
             ("Fahr die Rollos oben runter", "RolloSchnell"), ("Stripe im Bad auf Musik", "EffektSchnell"), ("Das Lied gefällt mir", "MusikGefaelltMir"),
             ("Spiel unsere Lieblingslieder", "MusikLieblingslieder"), ("Woher kommt die Musik", "MusikQuelle"), ("Spiel das Lied", "MusikWunsch"), ("Ich gehe ins Bett", "IchGeheInsBett"),
             ("Mach alles aus", "AllesAus"), ("Schalte oben schlafen ein", "SchlafmodusOG"), ("Wie warm ist es im Wohnzimmer", "TempWohnenKueche")]
SPRACHTESTS = [("Wie feucht ist es im Bad Yvonne", 8), ("Ist im Flur oben Licht an", 8), ("Wann geht das Außenlicht aus", 8)]
DOM = ("light|switch|binary_sensor|sensor|input_boolean|input_number|input_select|input_text|input_datetime|input_button|"
       "button|script|automation|climate|fan|media_player|humidifier|vacuum|select|number|cover|scene|counter|timer|todo|"
       "assist_satellite|conversation|weather|person|device_tracker|zone|lock|event|calendar|update|camera|siren|valve|"
       "text|remote|alarm_control_panel|sun|ai_task|stt|tts|wake_word")
REF_RE = re.compile(r"(?<![\w.])(" + DOM + r")\.([a-z0-9_]+)(?![\w*(])")

ergebnisse = []


def erg(prio, kat, test, status, info=""):
    """status: ok | warnung | fehler"""
    ergebnisse.append({"p": prio, "k": kat, "t": test, "s": status, "i": str(info)[:220]})


def pruef(prio, kat, test, bedingung, info="", warn=False):
    erg(prio, kat, test, "ok" if bedingung else ("warnung" if warn else "fehler"), "" if bedingung else info)


def alter_h(iso):
    try:
        return (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(iso)).total_seconds() / 3600
    except Exception:
        return 1e9


class WS:
    def __init__(self, s):
        self.s, self.n = s, 0

    async def auf(self):
        self.ws = await self.s.ws_connect(BASIS + "/api/websocket", max_msg_size=0)
        await self.ws.receive_json()
        await self.ws.send_json({"type": "auth", "access_token": TOKEN})
        await self.ws.receive_json()

    async def cmd(self, c, timeout=60):
        self.n += 1
        await self.ws.send_json({"id": self.n, **c})
        while True:
            r = await asyncio.wait_for(self.ws.receive_json(), timeout)
            if r.get("id") == self.n and r.get("type") == "result":
                return r


async def main():
    t0 = time.time()
    async with aiohttp.ClientSession(headers=H) as s:
        async def setze(state, attr):
            await s.post(BASIS + "/api/states/sensor.systemtest", json={"state": state, "attributes": attr})

        alt = {}
        try:
            async with s.get(BASIS + "/api/states/sensor.systemtest") as r:
                alt = (await r.json()).get("attributes", {}) if r.status == 200 else {}
        except Exception:
            pass
        await setze("läuft", {**alt, "friendly_name": "Systemtest", "icon": "mdi:progress-clock"})
        ws = WS(s)
        await ws.auf()

        # ---------- Grunddaten ----------
        S = {x["entity_id"]: x for x in (await ws.cmd({"type": "get_states"}))["result"]}
        reg = {e["entity_id"]: e for e in (await ws.cmd({"type": "config/entity_registry/list"}))["result"]}
        dienste = {f"{d}.{n}" for d, v in (await ws.cmd({"type": "get_services"}))["result"].items() for n in v}
        verwaist = {e for e, x in S.items() if x["attributes"].get("restored") or "browser_mod" in e}
        nv = lambda e: S.get(e, {}).get("state") in (None, "unavailable")

        # ---------- System: Konfiguration ----------
        try:
            async with s.post(BASIS + "/api/config/core/check_config", timeout=aiohttp.ClientTimeout(total=120)) as r:
                c = await r.json()
            pruef(1, "System", "Konfiguration gültig", c.get("result") == "valid", c.get("errors"))
        except Exception as e:
            erg(1, "System", "Konfiguration gültig", "fehler", e)

        # ---------- Integrationen ----------
        for e in (await ws.cmd({"type": "config_entries/get"}))["result"]:
            if e.get("disabled_by"):
                continue
            p = INTEG_PRIO.get(e["domain"], 3)
            pruef(p, "Integrationen", f"{e['domain']}: {e['title']}", e["state"] == "loaded", e["state"])

        # ---------- PRIO 1: Präsenzmelder ----------
        praesenz = sorted(e for e in S if e.startswith("binary_sensor.") and e not in verwaist and e not in ALTLASTEN
                          and (PRAESENZ_RE.search(e) or S[e]["attributes"].get("device_class") in ("occupancy", "motion", "presence")))
        for e in praesenz:
            pruef(1, "Präsenz & Licht", f"Präsenz {S[e]['attributes'].get('friendly_name', e)} verfügbar", not nv(e), S[e]["state"])
        # Bus-Antwort: KNX-Leseanfrage (GroupValueRead schaltet nichts), Antwort im Telegramm-Monitor abwarten
        ga_re = re.compile(r"^\d+/\d+/\d+$")
        knx_p = {reg[e]["unique_id"]: e for e in praesenz if reg.get(e, {}).get("platform") == "knx"
                 and ga_re.match(str(reg[e].get("unique_id", "")))}
        if knx_p:
            mon = WS(s)
            await mon.auf()
            await mon.cmd({"type": "knx/subscribe_telegrams"})
            await ws.cmd({"type": "call_service", "domain": "knx", "service": "read",
                          "service_data": {"address": list(knx_p)}})
            antwort, ende = {}, time.time() + 5
            while time.time() < ende and len(antwort) < len(knx_p):
                try:
                    m = await asyncio.wait_for(mon.ws.receive_json(), 1)
                except asyncio.TimeoutError:
                    continue
                t = m.get("event") or {}
                if t.get("telegramtype") == "GroupValueResponse" and t.get("destination") in knx_p:
                    antwort[t["destination"]] = t.get("source")
            await mon.ws.close()
            for ga, e in sorted(knx_p.items()):
                pruef(1, "Präsenz & Licht", f"Präsenz {S[e]['attributes'].get('friendly_name', e)} antwortet am Bus ({ga})",
                      ga in antwort, BEKANNT.get(e, "keine Antwort auf Leseanfrage – Melder/Bus prüfen"), warn=e in BEKANNT)
        # Plausibilität: hängt auf "besetzt" (26.10.: Flur OG 2 Tage an → Haus nie leer, Licht blieb beim Weggehen an)
        durchgang = ("flur", "gastebad", "sauna", "einfahrt", "aussen")
        for e in praesenz:
            if not nv(e) and S[e]["state"] == "on":
                h = alter_h(S[e]["last_changed"])
                grenze = 2 if any(d in e for d in durchgang) else 14
                pruef(1, "Präsenz & Licht", f"Präsenz {S[e]['attributes'].get('friendly_name', e)} hängt nicht auf 'besetzt'",
                      h < grenze, f"seit {h:.0f} h ununterbrochen besetzt – Melder prüfen", warn=grenze == 14)
        # Plausibilität: lange keine Bewegung -> Melder evtl. tot
        for e in praesenz:
            if not nv(e) and S[e]["state"] == "off":
                h = alter_h(S[e]["last_changed"])
                pruef(1, "Präsenz & Licht", f"Präsenz {S[e]['attributes'].get('friendly_name', e)} meldet Bewegung (48 h)",
                      h < 48, f"seit {h:.0f} h keine Bewegung", warn=True)

        # Handys: meldet sich ein Handy "zu Hause" seit > 2 h nicht, zählt es nicht als Anwesenheit (Hinweis, 26.10.)
        for p in sorted(x for x in S if x.startswith("person.")):
            q = S[p]["attributes"].get("source")
            if S[p]["state"] == "home" and q in S:
                h = alter_h(S[q]["last_updated"])
                erg(2, "Anwesenheit", f"Handy {S[p]['attributes'].get('friendly_name', p)} meldet sich", "ok" if h < 2 else "info",
                    "" if h < 2 else f"seit {h:.1f} h keine Meldung – zählt nicht als zu Hause (HA-App: Standort immer erlauben)")
        jih = S.get("binary_sensor.jemand_im_haus", {})
        pruef(1, "Präsenz & Licht", "Anwesenheit (Jemand im Haus) verfügbar", jih.get("state") in ("on", "off"), jih.get("state"))

        # ---------- PRIO 1: Lichter ----------
        lichter = sorted(e for e in S if e.startswith("light.") and e not in verwaist and e not in ALTLASTEN)
        weg = [S[e]["attributes"].get("friendly_name", e) for e in lichter if nv(e)]
        pruef(1, "Präsenz & Licht", f"Alle {len(lichter)} Lichter erreichbar", not weg, ", ".join(weg))

        # Außensauna-Stripe: kein Alarm-Blinkeffekt gespeichert, wenn kein Alarm läuft (Fehler 24.10.: blinkte dauerhaft)
        alarm_laeuft = int(S.get("automation.kinder_wach_alarm_sauna_decke_blinkt_bei_bewegung_flur_og", {})
                           .get("attributes", {}).get("current", 0) or 0) > 0
        try:
            async with s.get("http://192.168.11.192/json/state", timeout=aiohttp.ClientTimeout(total=5)) as r:
                fx = (await r.json(content_type=None))["seg"][0]["fx"]
            pruef(1, "Präsenz & Licht", "Außensauna-Stripe ohne Alarm-Blinkeffekt", fx == 0 or alarm_laeuft,
                  f"Effekt {fx} gespeichert – blinkt beim nächsten Einschalten")
        except Exception as e:
            erg(1, "Präsenz & Licht", "Außensauna-Stripe ohne Alarm-Blinkeffekt", "fehler", f"WLED nicht erreichbar: {e}")

        # ---------- Pflicht-Entitäten ----------
        for e, (p, k) in PFLICHT.items():
            st = S.get(e, {}).get("state")
            pruef(p, k, f"{S.get(e, {}).get('attributes', {}).get('friendly_name', e)}", st not in (None, "unavailable"),
                  "fehlt" if st is None else st)

        # ---------- Heizung & Klima ----------
        for e in sorted(x for x in S if x.startswith("climate.") and x not in ALTLASTEN and x not in verwaist):
            pruef(2, "Heizung & Klima", f"Heizung {S[e]['attributes'].get('friendly_name', e)}", not nv(e), S[e]["state"])
        # KNX-Raumwerte (Temperatur/Feuchte/Taupunkt) müssen frisch sein
        for e in sorted(x for x in S if reg.get(x, {}).get("platform") == "knx" and x.startswith(
                ("sensor.temperatur_", "sensor.feuchte_", "sensor.taupunkt_", "sensor.helligkeit_", "sensor.absolute_feuchte_"))):
            h = alter_h(S[e].get("last_reported", S[e]["last_updated"]))
            # Timberwolf sendet bei ausgefallenem Sensor den letzten Wert weiter → bei Feuchte/Taupunkt auch "unverändert" prüfen
            if e.startswith(("sensor.feuchte_", "sensor.taupunkt_")):
                h = max(h, alter_h(S[e]["last_changed"]) - 6)   # > 12 h unverändert ergibt > 6 h → Warnung/Fehler
            gut = not nv(e) and S[e]["state"] != "unknown" and h < 6   # KNX sendet oft nur bei Änderung: 6–24 h = Warnung
            grund = next((g for endung, g in BEKANNT.items() if e.endswith(endung)), None)
            erg(2, "Heizung & Klima", f"Raumwert {S[e]['attributes'].get('friendly_name', e)} aktuell",
                "ok" if gut else ("warnung" if grund or h < 24 or e.startswith(("sensor.helligkeit_", "sensor.absolute_feuchte_")) else "fehler"),
                "" if gut else f"{S[e]['state']}, {h:.0f} h alt" + (f" ({grund})" if grund else ""))

        # ---------- KNX allgemein ----------
        knx_weg = sorted(e for e, r in reg.items() if r["platform"] == "knx" and S.get(e, {}).get("state") == "unavailable"
                         and e not in ALTLASTEN and e not in verwaist and not e.startswith("sensor."))
        pruef(1, "System", "KNX: alle Aktoren/Melder verfügbar", not knx_weg, knx_weg[:12])

        # ---------- Automationen & Skripte: Referenzen, Zustand, Protokolle ----------
        autos = sorted(e for e in S if e.startswith("automation.") and e not in verwaist)
        traces = (await ws.cmd({"type": "trace/list", "domain": "automation"})).get("result") or []
        grenze = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=24)).isoformat()
        fehl_tr, lauf_ok = {}, {}
        for x in traces:
            start = x.get("timestamp", {}).get("start", "")
            if x.get("error") or x.get("script_execution") == "error":
                if start > grenze:
                    fehl_tr.setdefault(x["item_id"], x.get("error") or "Fehler")
            elif x.get("script_execution") == "finished":
                lauf_ok[x["item_id"]] = max(lauf_ok.get(x["item_id"], ""), start)
        # Konfigurationen holen; Szenen, die erst zur Laufzeit per scene.create entstehen, sammeln
        cfgs = {}
        for e in autos + [x for x in S if x.startswith("script.") and x not in verwaist]:
            try:
                typ = "automation/config" if e.startswith("automation.") else "script/config"
                cfgs[e] = json.dumps((await ws.cmd({"type": typ, "entity_id": e}))["result"]["config"],
                                     ensure_ascii=False).replace("states.", "")
            except Exception:
                cfgs[e] = ""
        laufzeit = {"scene." + x for t in cfgs.values() for x in re.findall(r'"scene_id": "(\w+)"', t)} | EREIGNISSE

        def fehlende(txt, selbst):
            refs = {f"{d}.{i}" for d, i in REF_RE.findall(txt) if not i.endswith("_")}
            return sorted(r for r in refs if r not in S and r not in dienste and r not in laufzeit and r != selbst)

        p1_autos = 0
        for e in autos:
            a = S[e]["attributes"]
            name = a.get("friendly_name", e)
            txt = cfgs.get(e, "")
            fehlt = fehlende(txt, e)
            if S[e]["state"] == "off":   # bewusst ausgeschaltet: nur Hinweis
                erg(3, "Ausgeschaltete Automationen", f"„{name}“ ist ausgeschaltet", "info",
                    ("fehlende Entitäten: " + ", ".join(fehlt)) if fehlt else "")
                continue
            praesenz_licht = bool(re.search(r"binary_sensor\.\w*" + PRAESENZ_RE.pattern, txt)) and "light." in txt
            p, k = (1, "Präsenz & Licht") if praesenz_licht else (2, "Automationen")
            p1_autos += praesenz_licht
            if S[e]["state"] == "unavailable":
                erg(p, k, f"Automation „{name}“ geladen", "fehler", "nicht verfügbar")
                continue
            # fehlende Entitäten: deaktivierte Registry-Einträge = Warnung, ganz unbekannt = Fehler
            unbekannt = [r for r in fehlt if r not in reg]
            erg(p, k, f"„{name}“: Entitäten vorhanden", "fehler" if unbekannt else ("warnung" if fehlt else "ok"),
                ", ".join(fehlt))
            aid = a.get("id")
            erg(p, k, f"„{name}“: ohne Laufzeitfehler (24 h)", "fehler" if aid in fehl_tr else "ok", fehl_tr.get(aid, ""))
            if praesenz_licht and e not in SELTEN:
                h = alter_h(a.get("last_triggered") or "")
                pruef(p, k, f"„{name}“: lief zuletzt erfolgreich (72 h)", h < 72,
                      "nie ausgelöst" if h > 1e8 else f"letzte Auslösung vor {h:.0f} h", warn=True)
        erg(1, "Präsenz & Licht", f"{p1_autos} Präsenz-Licht-Automationen erkannt", "ok" if p1_autos else "fehler",
            "" if p1_autos else "keine gefunden")
        for e in sorted(x for x in cfgs if x.startswith("script.") and cfgs[x]):
            fehlt = fehlende(cfgs[e], e)
            unbekannt = [r for r in fehlt if r not in reg]
            erg(2, "Skripte", f"Skript „{S[e]['attributes'].get('friendly_name', e)}“: Entitäten vorhanden",
                "fehler" if unbekannt else ("warnung" if fehlt else "ok"), ", ".join(fehlt))

        # ---------- Dienste, Vorlagen ----------
        fehlt = [d for d in DIENSTE if d not in dienste]
        pruef(2, "System", f"{len(DIENSTE)} wichtige Dienste vorhanden", not fehlt, fehlt)
        tpl = [e for e, r in reg.items() if r["platform"] == "template" and e in S and e not in verwaist]
        kaputt = sorted(e for e in tpl if S[e]["state"] in ("unavailable", "unknown") and not e.startswith(("button.", "image.")))
        pruef(2, "System", f"{len(tpl)} Vorlagen-Sensoren liefern Werte", not kaputt, kaputt[:10], warn=len(kaputt) <= 2)
        z = S.get("sensor.sprache_zustand", {}).get("attributes", {}).get("text", "")
        pruef(3, "Komfort", "Sprach-Zustandsblock gefüllt", len(z) > 300 and "Raumklima" in z, f"{len(z)} Zeichen")

        # ---------- HA-Log ----------
        log = (await ws.cmd({"type": "system_log/list"}))["result"]
        harmlos = ("aviationweather", "snitun", "upnp", "browser_mod", "Task exception was never retrieved", "metar")
        neu = [f"{x['name']}: {str(x['message'][0])[:100]}" for x in log if x["level"] == "ERROR" and time.time() - x["timestamp"] < 7200
               and not any(h in (x["name"] + str(x["message"])) for h in harmlos)]
        pruef(2, "System", "Keine neuen Fehler im HA-Log (2 h)", not neu, " | ".join(neu[:4]), warn=True)
        # Vorlagen-Schleifen bremsen den Pi aus (25.10.: netz_upload > 4600 Neuberechnungen)
        schleife = [str(x["message"][0])[60:140] for x in log if "loop detected" in str(x["message"]).lower()
                    and time.time() - x["timestamp"] < 1800]
        pruef(2, "System", "Keine Endlosschleifen in Vorlagen (30 min)", not schleife, " | ".join(schleife[:2]))
        # DNS + Nabu-Casa-Cloud (Spracherkennung/-ausgabe hängt daran; 25.10.: DNS-Zeitüberschreitung → Sprache tot)
        try:
            t_dns = time.time()
            await asyncio.get_running_loop().getaddrinfo("api.nabucasa.com", 443)
            d_dns = time.time() - t_dns
            pruef(2, "System", "DNS: Cloud-Adresse auflösbar (< 1 s)", d_dns < 1, f"{d_dns:.1f} s", warn=True)
        except Exception as e:
            erg(2, "System", "DNS: Cloud-Adresse auflösbar (< 1 s)", "fehler", e)
        pruef(2, "System", "Cloud-Spracherkennung verfügbar", not nv("stt.home_assistant_cloud"),
              S.get("stt.home_assistant_cloud", {}).get("state"))

        # ---------- Pi, Backup ----------
        def zahl(e, d=0.0):
            try:
                return float(S[e]["state"])
            except Exception:
                return d
        pruef(2, "System", "Pi-Temperatur < 75 °C", zahl("sensor.system_monitor_prozessortemperatur") < 75,
              S.get("sensor.system_monitor_prozessortemperatur", {}).get("state"), warn=True)
        pruef(2, "System", "Speicher < 85 % belegt", zahl("sensor.system_monitor_massenspeicher_auslastung") < 85,
              S.get("sensor.system_monitor_massenspeicher_auslastung", {}).get("state"), warn=True)
        b = S.get("sensor.backup_letztes_erfolgreiches_automatisches_backup", {}).get("state", "")
        pruef(2, "System", "Backup jünger als 36 h", alter_h(b) < 36, b or "kein Backup", warn=True)

        # ---------- Komfort: Batterien, Geräte ----------
        leer = [f"{S[e]['attributes'].get('friendly_name', e)} {S[e]['state']} %" for e in S
                if S[e]["attributes"].get("device_class") == "battery" and e.startswith("sensor.") and zahl(e, 100) < 20]
        pruef(3, "Komfort", "Batterien > 20 %", not leer, ", ".join(leer), warn=True)

        # ---------- Sprache: Satzerkennung (Testmodus, führt NICHTS aus) ----------
        try:
            r = await ws.cmd({"type": "conversation/agent/homeassistant/debug", "language": "de",
                              "sentences": [s_ for s_, _ in SATZTESTS]})
            for (satz, soll), x in zip(SATZTESTS, r["result"]["results"]):
                ist = ((x or {}).get("intent") or {}).get("name")
                pruef(3, "Sprache", f"Satz „{satz}“ → {soll}", ist == soll, f"erkannt als {ist}")
                # Schnellbefehle: Ziel-Lampen müssen existieren
                d_ = (x or {}).get("details") or {}
                ziel = (d_.get("licht") or d_.get("raum") or {}).get("value", "")
                fehlt = [z for z in str(ziel).split(",") if z and z not in S]
                if ziel:
                    pruef(3, "Sprache", f"Satz „{satz}“: Lampen vorhanden", not fehlt, fehlt)
        except Exception as e:
            erg(3, "Sprache", "Satzerkennung", "fehler", e)
        # gelernte Kurzbefehle: Ziele müssen echte Geräte sein (Fehler bis 25.10.: ziel "entity_id")
        try:
            r = await ws.cmd({"type": "call_service", "domain": "todo", "service": "get_items", "return_response": True,
                              "target": {"entity_id": "todo.gelernte_sprachbefehle"}})
            kaputt = []
            for it in r["result"]["response"]["todo.gelernte_sprachbefehle"]["items"]:
                try:
                    z = json.loads(it.get("description") or "{}").get("ziel") or []
                except ValueError:
                    z = []
                z = [z] if isinstance(z, str) else z
                if not z or any(x not in S for x in z):
                    kaputt.append(it["summary"])
            pruef(3, "Sprache", "Gelernte Kurzbefehle haben gültige Ziele", not kaputt, kaputt[:5])
        except Exception as e:
            erg(3, "Sprache", "Gelernte Kurzbefehle lesbar", "fehler", e)
        # Effekt-Skript: alle deutschen Effektnamen gibt es im WLED
        try:
            txt = open("/config/packages/sprache_effekte.yaml", encoding="utf-8").read()
            block = txt.split("synonyme:")[1].split("\n      farben:")[0]
            namen = set(re.findall(r":\s*(.+)\s*$", block, re.M))
            liste = S.get("light.wled_kuche", {}).get("attributes", {}).get("effect_list") or []
            fehlt = sorted(n.strip() for n in namen if n.strip() not in liste)
            pruef(3, "Sprache", f"Effekt-Skript: {len(namen)} Effektnamen im WLED vorhanden", liste and not fehlt, fehlt or "WLED Küche ohne Liste")
        except Exception as e:
            erg(3, "Sprache", "Effekt-Skript lesbar", "fehler", e)
        # Musik-Stripe Bad Yvonne: Mikrofon aktiv (Audio-Reaktion an, nur lesen)
        try:
            async with s.get("http://192.168.11.51/json/info", timeout=aiohttp.ClientTimeout(total=5)) as r:
                u_ = (await r.json(content_type=None)).get("u", {})
            quelle = " ".join(str(x) for x in u_.get("Audio Source", []))
            pruef(3, "Sprache", "Stripe Bad Yvonne: Mikrofon für Musik-Effekte aktiv",
                  "Audio Source" in u_ and "quiet" not in quelle, quelle or "Audio-Reaktion aus", warn=True)
        except Exception as e:
            erg(3, "Sprache", "Stripe Bad Yvonne: Mikrofon für Musik-Effekte aktiv", "warnung", f"nicht erreichbar: {e}")
        # für Sprache freigegebene Geräte dürfen nicht tot sein (verwirren Claude und die Satzerkennung)
        ex = (await ws.cmd({"type": "homeassistant/expose_entity/list"}))["result"]["exposed_entities"]
        tot = sorted(e for e, v in ex.items() if v.get("conversation") and e in S and S[e]["state"] == "unavailable")
        pruef(3, "Sprache", "Keine nicht erreichbaren Geräte für Sprache freigegeben", not tot, tot[:10], warn=True)
        pruef(3, "Sprache", "Voice PE: Sprechpausen-Erkennung geduldig (relaxed)",
              S.get("select.home_assistant_voice_0adb1a_sprechpausen_erkennung", {}).get("state") == "relaxed",
              S.get("select.home_assistant_voice_0adb1a_sprechpausen_erkennung", {}).get("state"))
        pruef(3, "Sprache", "Voice PE: Weckwort Ludwig aktiv",
              S.get("select.home_assistant_voice_0adb1a_aktivierungswort", {}).get("state") == "Ludwig",
              S.get("select.home_assistant_voice_0adb1a_aktivierungswort", {}).get("state"), warn=True)
        pruef(3, "Sprache", "Ludwig-Modell vorhanden", os.path.exists("/config/www/ludwig/ludwig.tflite") and os.path.exists("/config/www/ludwig/ludwig.json"), "Datei fehlt")
        pruef(3, "Sprache", "Effekt-Skript für Sprache freigegeben", ex.get("script.licht_effekt", {}).get("conversation"), "nicht freigegeben")

        # ---------- Sprache (optional, nur Fragen) ----------
        if SPRACHE:
            for satz, limit in SPRACHTESTS:
                try:
                    s0 = time.time()
                    r = await ws.cmd({"type": "conversation/process", "text": satz, "language": "de",
                                      "agent_id": "conversation.claude_conversation"}, timeout=60)
                    d = time.time() - s0
                    sp = r["result"]["response"]["speech"]["plain"]["speech"]
                    pruef(3, "Sprache", f"„{satz}“ < {limit} s", d < limit and len(sp) > 5 and "fehler" not in sp.lower(),
                          f"{d:.1f} s – {sp[:80]}")
                except Exception as e:
                    erg(3, "Sprache", f"„{satz}“", "fehler", e)

        # ---------- Ergebnis ----------
        ergebnisse.sort(key=lambda x: ({"fehler": 0, "warnung": 1, "info": 2, "ok": 3}[x["s"]], x["p"], x["k"]))
        nf = sum(x["s"] == "fehler" for x in ergebnisse)
        nw = sum(x["s"] == "warnung" for x in ergebnisse)
        kf = sum(x["s"] == "fehler" and x["p"] == 1 for x in ergebnisse)
        kats = {}
        for x in ergebnisse:
            k = kats.setdefault(f"{x['p']}|{x['k']}", {"ok": 0, "warnung": 0, "fehler": 0, "info": 0})
            k[x["s"]] += 1
        zustand = "ok" if nf == 0 and nw == 0 else (f"{nf} Fehler" if nf else f"{nw} Warnungen")
        await setze(zustand, {
            "friendly_name": "Systemtest", "icon": "mdi:clipboard-check-outline" if nf == 0 else "mdi:clipboard-alert-outline",
            "zeit": dt.datetime.now().strftime("%d.%m. %H:%M"), "dauer": round(time.time() - t0),
            "gesamt": len(ergebnisse), "bestanden": sum(x["s"] in ("ok", "info") for x in ergebnisse),
            "fehler_anzahl": nf, "warnungen": nw,
            "kritisch": kf, "kategorien": kats,
            "probleme": [{k: x[k] for k in ("p", "k", "t", "s", "i")} for x in ergebnisse if x["s"] != "ok"][:80],
            "fehler": [f"P{x['p']} {x['t']}: {x['i']}" for x in ergebnisse if x["s"] == "fehler"][:40],
        })
        with open(os.path.join(HIER, "systemtest_letzter.json"), "w", encoding="utf-8") as f:
            json.dump(ergebnisse, f, ensure_ascii=False, indent=0)


if __name__ == "__main__":
    asyncio.run(main())
