import requests
import datetime
import uuid
import os
import pytz
import json
from icalendar import Calendar, Event

# ── Konfiguration ──────────────────────────────────────────────────────────────
SERVER   = "ruckert-gym.webuntis.com"
SCHOOL   = "ruckert-gym"
USERNAME = os.environ["WEBUNTIS_USER"]
PASSWORD = os.environ["WEBUNTIS_PASS"]
TIMEZONE = pytz.timezone("Europe/Berlin")
OUTPUT   = "calendar.ics"
BASE_URL = f"https://{SERVER}/WebUntis/jsonrpc.do"
# ──────────────────────────────────────────────────────────────────────────────

session_id  = None
school_name = None   # wird beim Login gesetzt
http        = requests.Session()
http.headers.update({"User-Agent": "WebUntis-iCal-Export/1.0"})

def rpc(method, params=None):
    payload = {
        "id":      "req",
        "method":  method,
        "params":  params or {},
        "jsonrpc": "2.0",
    }
    if session_id:
        http.cookies.set("JSESSIONID", session_id)
    r = http.post(
        BASE_URL,
        json=payload,
        params={"school": school_name or SCHOOL},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise Exception(f"WebUntis API Fehler [{data['error'].get('code')}]: {data['error'].get('message')}")
    return data.get("result")

def find_school_name():
    return SCHOOL

def login():
    global session_id, school_name
    school_name = find_school_name()
    print(f"Schulname gefunden: '{school_name}'")
    result = rpc("authenticate", {
        "user":     USERNAME,
        "password": PASSWORD,
        "client":   "iCal-Export",
    })
    session_id = result["sessionId"]
    print(f"Login erfolgreich.")
    return result

def logout():
    try:
        rpc("logout")
        print("Logout erfolgreich.")
    except Exception:
        pass

def get_student_id():
    """Holt die eigene Schüler-ID über getStudents."""
    result = rpc("getStudents")
    if not result:
        raise Exception("Keine Schülerdaten gefunden.")
    # Debug: zeige Felder und ersten Eintrag
    print(f"Verfügbare Felder: {list(result[0].keys())}")
    print(f"Erster Eintrag: {result[0]}")
    # Finde den eigenen Eintrag per Benutzername (verschiedene Felder probieren)
    for s in result:
        for field in ("name", "longName", "key", "login"):
            if s.get(field, "").lower() == USERNAME.lower():
                print(f"Gefunden via Feld '{field}': ID={s['id']}")
                return s["id"]
    raise Exception(f"Konnte Schüler-ID nicht ermitteln. Benutzername '{USERNAME}' nicht in Liste gefunden.")

def get_timetable(student_id, start: datetime.date, end: datetime.date):
    return rpc("getTimetable", {
        "options": {
            "id":               int(datetime.datetime.now().timestamp()),
            "element":          {"id": student_id, "type": 5},
            "startDate":        int(start.strftime("%Y%m%d")),
            "endDate":          int(end.strftime("%Y%m%d")),
            "showLsText":       True,
            "showStudentgroup": True,
            "showLsNumber":     True,
            "showSubstText":    True,
            "showInfo":         True,
            "showBooking":      True,
        }
    })

def parse_dt(date_int, time_int) -> datetime.datetime:
    date_str = str(date_int)
    time_str = str(time_int).zfill(4)
    dt = datetime.datetime.strptime(date_str + time_str, "%Y%m%d%H%M")
    return TIMEZONE.localize(dt)

def lesson_type(lesson) -> str:
    code = lesson.get("code", 0)
    if code == 1:
        return "CANCELLED"
    if code == 2:
        return "IRREGULAR"
    if lesson.get("lstype") == "oh":
        return "ADDITIONAL"
    return "REGULAR"

def build_summary(lesson, ltype) -> str:
    subjects = ", ".join(s["name"] for s in lesson.get("su", [])) or "Unbekannt"
    prefix = {
        "CANCELLED":  "❌ AUSFALL – ",
        "IRREGULAR":  "🔄 Vertretung – ",
        "ADDITIONAL": "➕ ",
        "REGULAR":    "",
    }[ltype]
    return f"{prefix}{subjects}"

def build_description(lesson, ltype) -> str:
    lines = []
    teachers = ", ".join(t["name"] for t in lesson.get("te", []))
    if teachers:
        lines.append(f"Lehrer: {teachers}")
    rooms = ", ".join(r["name"] for r in lesson.get("ro", []))
    if rooms:
        lines.append(f"Raum: {rooms}")
    classes = ", ".join(c["name"] for c in lesson.get("kl", []))
    if classes:
        lines.append(f"Klasse: {classes}")
    if lesson.get("info"):
        lines.append(f"Info: {lesson['info']}")
    if lesson.get("substText"):
        lines.append(f"Vertretungstext: {lesson['substText']}")
    if lesson.get("lstext"):
        lines.append(f"Text: {lesson['lstext']}")
    return "\n".join(lines)

def lesson_to_event(lesson) -> Event:
    ltype    = lesson_type(lesson)
    start_dt = parse_dt(lesson["date"], lesson["startTime"])
    end_dt   = parse_dt(lesson["date"], lesson["endTime"])

    event = Event()
    event.add("uid",         str(uuid.uuid4()))
    event.add("summary",     build_summary(lesson, ltype))
    event.add("description", build_description(lesson, ltype))
    event.add("dtstart",     start_dt)
    event.add("dtend",       end_dt)
    event.add("dtstamp",     datetime.datetime.now(tz=pytz.utc))

    rooms = ", ".join(r["name"] for r in lesson.get("ro", []))
    if rooms:
        event.add("location", rooms)
    if ltype == "CANCELLED":
        event.add("status", "CANCELLED")

    return event

def main():
    print("Verbinde mit WebUntis...")
    login()
    try:
        student_id = get_student_id()
        print(f"Schüler-ID: {student_id}")

        today = datetime.date.today()
        end   = today + datetime.timedelta(weeks=8)
        print(f"Hole Stunden von {today} bis {end}...")

        timetable = get_timetable(student_id, today, end)
        print(f"{len(timetable)} Stunden gefunden.")

        cal = Calendar()
        cal.add("prodid",   "-//WebUntis iCal Export//DE")
        cal.add("version",  "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("x-wr-calname",  "Stundenplan")
        cal.add("x-wr-timezone", "Europe/Berlin")
        cal.add("refresh-interval;value=duration", "PT30M")

        count = 0
        for lesson in timetable:
            try:
                cal.add_component(lesson_to_event(lesson))
                count += 1
            except Exception as e:
                print(f"  ⚠ Stunde übersprungen: {e}")

        print(f"{count} Stunden verarbeitet.")
        with open(OUTPUT, "wb") as f:
            f.write(cal.to_ical())
        print(f"✅ Kalender gespeichert als '{OUTPUT}'.")

    finally:
        logout()

if __name__ == "__main__":
    main()
