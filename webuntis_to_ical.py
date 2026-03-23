import webuntis.session as webuntis
import datetime
from icalendar import Calendar, Event
import pytz
import os
import uuid

# ── Konfiguration ──────────────────────────────────────────────────────────────
SERVER   = "rueckert-gym.webuntis.com"
SCHOOL   = "Rückert-Gymnasium"
USERNAME = os.environ["WEBUNTIS_USER"]
PASSWORD = os.environ["WEBUNTIS_PASS"]
TIMEZONE = pytz.timezone("Europe/Berlin")
OUTPUT   = "calendar.ics"
# ──────────────────────────────────────────────────────────────────────────────

# Farben je nach Stundentyp
TYPE_COLORS = {
    "REGULAR":      "4A90D9",   # Blau  – normaler Unterricht
    "CANCELLED":    "E74C3C",   # Rot   – Ausfall
    "IRREGULAR":    "F39C12",   # Orange – Vertretung / Änderung
    "ADDITIONAL":   "27AE60",   # Grün  – Zusatzstunde
}

def lesson_type(lesson) -> str:
    """Gibt den Typ einer Stunde zurück."""
    code = getattr(lesson, "code", None)
    if code == "cancelled":
        return "CANCELLED"
    if code == "irregular":
        return "IRREGULAR"
    lstype = getattr(lesson, "lstype", None)
    if lstype == "oh":
        return "ADDITIONAL"
    return "REGULAR"

def build_summary(lesson, ltype: str) -> str:
    """Baut den Kalendertitel zusammen."""
    subjects = ", ".join(s.name for s in lesson.subjects) if lesson.subjects else "Unbekannt"
    prefix = {
        "CANCELLED":  "❌ AUSFALL – ",
        "IRREGULAR":  "🔄 Vertretung – ",
        "ADDITIONAL": "➕ ",
        "REGULAR":    "",
    }[ltype]
    return f"{prefix}{subjects}"

def build_description(lesson, ltype: str) -> str:
    """Baut die Beschreibung zusammen."""
    lines = []
    if lesson.teachers:
        lines.append("Lehrer: " + ", ".join(t.name for t in lesson.teachers))
    if lesson.rooms:
        lines.append("Raum: " + ", ".join(r.name for r in lesson.rooms))
    if lesson.classes:
        lines.append("Klasse: " + ", ".join(c.name for c in lesson.classes))
    info = getattr(lesson, "info", None)
    if info:
        lines.append(f"Info: {info}")
    sub_text = getattr(lesson, "substText", None)
    if sub_text:
        lines.append(f"Vertretungstext: {sub_text}")
    return "\n".join(lines)

def lesson_to_event(lesson) -> Event:
    ltype = lesson_type(lesson)

    # Datum + Uhrzeit zusammenbauen
    date_str = str(lesson.start.date())      # z.B. "2025-03-10"
    start_t  = lesson.start                  # datetime
    end_t    = lesson.end

    start_dt = TIMEZONE.localize(start_t) if start_t.tzinfo is None else start_t
    end_dt   = TIMEZONE.localize(end_t)   if end_t.tzinfo   is None else end_t

    event = Event()
    event.add("uid",     str(uuid.uuid4()))
    event.add("summary", build_summary(lesson, ltype))
    event.add("description", build_description(lesson, ltype))
    event.add("dtstart", start_dt)
    event.add("dtend",   end_dt)
    event.add("dtstamp", datetime.datetime.now(tz=pytz.utc))

    # Farbe als X-Property (wird von Google Kalender ignoriert, aber von anderen Apps genutzt)
    color = TYPE_COLORS.get(ltype, "4A90D9")
    event.add("color", f"#{color}")

    if lesson.rooms:
        event.add("location", ", ".join(r.name for r in lesson.rooms))

    # Ausfall-Stunden als "abgesagt" markieren
    if ltype == "CANCELLED":
        event.add("status", "CANCELLED")

    return event

def main():
    print("Verbinde mit WebUntis...")
    with webuntis.Session(
        server=SERVER,
        school=SCHOOL,
        username=USERNAME,
        password=PASSWORD,
        useKeyring=False,
    ) as session:
        session.login()
        print("Login erfolgreich.")

        # Zeitraum: heute bis in 8 Wochen
        today = datetime.date.today()
        end   = today + datetime.timedelta(weeks=8)

        print(f"Hole Stunden von {today} bis {end}...")
        timetable = session.timetable(start=today, end=end).filter(type="student")

        cal = Calendar()
        cal.add("prodid", "-//WebUntis iCal Export//DE")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("x-wr-calname", "Stundenplan")
        cal.add("x-wr-timezone", "Europe/Berlin")
        cal.add("refresh-interval;value=duration", "PT30M")  # Kalender-Apps alle 30 min aktualisieren

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

if __name__ == "__main__":
    main()
