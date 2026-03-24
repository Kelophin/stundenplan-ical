import requests
import os
import datetime

SERVER   = "ruckert-gym.webuntis.com"
SCHOOL   = "ruckert-gym"
USERNAME = os.environ["WEBUNTIS_USER"]
PASSWORD = os.environ["WEBUNTIS_PASS"]
BASE_URL = f"https://{SERVER}/WebUntis/jsonrpc.do"

http = requests.Session()
http.headers.update({"User-Agent": "WebUntis-iCal-Export/1.0"})
session_id = None

def rpc(method, params=None):
    payload = {"id": "req", "method": method, "params": params or {}, "jsonrpc": "2.0"}
    if session_id:
        http.cookies.set("JSESSIONID", session_id)
    r = http.post(BASE_URL, json=payload, params={"school": SCHOOL},
                  headers={"Content-Type": "application/json"}, timeout=30)
    r.raise_for_status()
    return r.json()

# Login
resp = rpc("authenticate", {"user": USERNAME, "password": PASSWORD, "client": "debug"})
session_id = resp["result"]["sessionId"]
person_id  = resp["result"]["personId"]
klasse_id  = resp["result"]["klasseId"]
print(f"personId={person_id}, klasseId={klasse_id}")

today = datetime.date.today()
end   = today + datetime.timedelta(days=14)
start_int = int(today.strftime("%Y%m%d"))
end_int   = int(end.strftime("%Y%m%d"))

# Test 1: Timetable mit Klassen-ID (type 1)
print("\n=== getTimetable type=1 (Klasse) ===")
r = rpc("getTimetable", {"options": {
    "id": 1, "element": {"id": klasse_id, "type": 1},
    "startDate": start_int, "endDate": end_int,
    "showLsText": True, "showSubstText": True, "showInfo": True,
}})
if "error" in r:
    print(f"Fehler: {r['error']}")
else:
    lessons = r["result"] or []
    print(f"{len(lessons)} Stunden")
    cancelled = [l for l in lessons if l.get("code") == 1]
    irregular = [l for l in lessons if l.get("code") == 2]
    print(f"  Ausfälle: {len(cancelled)}, Vertretungen: {len(irregular)}")
    if cancelled: print(f"  Beispiel Ausfall: {cancelled[0]}")
    if irregular: print(f"  Beispiel Vertretung: {irregular[0]}")

# Test 2: Substitutions Endpunkt
print("\n=== getSubstitutions ===")
r = rpc("getSubstitutions", {"startDate": start_int, "endDate": end_int, "departmentId": 0})
if "error" in r:
    print(f"Fehler: {r['error']}")
else:
    subs = r["result"] or []
    print(f"{len(subs)} Vertretungen gefunden")
    if subs: print(f"Beispiel: {subs[0]}")

rpc("logout")
print("\nDone.")
