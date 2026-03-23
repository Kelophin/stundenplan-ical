import requests
import os

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
print("=== LOGIN ===")
resp = rpc("authenticate", {"user": USERNAME, "password": PASSWORD, "client": "debug"})
print(resp)
session_id = resp["result"]["sessionId"]

# Methoden testen
methods = [
    ("getCurrentUser",   {}),
    ("getPersonId",      {"type": 5, "id": 0, "date": 0}),
    ("getStudents",      {}),
    ("getClasses",       {}),
    ("getSubjects",      {}),
    ("getTimegridUnits", {}),
    ("getStatusData",    {}),
    ("getLatestImportTime", {}),
    ("getTimetable",     {"id": 0, "type": 5}),
]

print("\n=== API METHODEN TEST ===")
for method, params in methods:
    try:
        result = rpc(method, params)
        if "error" in result:
            print(f"❌ {method}: {result['error']}")
        else:
            r = result.get("result")
            preview = str(r)[:120] if r else "None"
            print(f"✅ {method}: {preview}")
    except Exception as e:
        print(f"💥 {method}: {e}")

# Logout
rpc("logout")
print("\n=== LOGOUT ===")
