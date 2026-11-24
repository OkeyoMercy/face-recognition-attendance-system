import os
import django
import datetime

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'attendance_project.settings')
django.setup()

from attendance_app.models import Unit, Timetable

def setup_data():
    # 1. Create Units
    units_data = [
        ("CIR 101", "Discrete Structures"),
        ("MAS 103", "Introduction to Statistics"),
        ("CCS 104", "Fundamentals of Computing"),
    ]

    units = {}
    for code, name in units_data:
        unit, created = Unit.objects.get_or_create(code=code, defaults={'name': name, 'hours_per_week': 6})
        units[code] = unit
        if created:
            print(f"Created Unit: {code}")
        else:
            print(f"Unit {code} already exists.")

    # 2. Setup Timetable (18 hours total per week, 6 per unit)
    # We'll split each unit into two 3-hour sessions
    timetable_data = [
        # CIR 101
        (units["CIR 101"], "Monday", "08:00", "11:00", "TB2"),
        (units["CIR 101"], "Wednesday", "11:00", "14:00", "NL5"),

        # MAS 103
        (units["MAS 103"], "Monday", "11:00", "14:00", "NL5"),
        (units["MAS 103"], "Tuesday", "08:00", "11:00", "LAB3"),

        # CCS 104
        (units["CCS 104"], "Tuesday", "11:00", "14:00", "TB2"),
        (units["CCS 104"], "Wednesday", "08:00", "11:00", "LAB3"),
    ]

    for unit, day, start, end, venue in timetable_data:
        start_t = datetime.datetime.strptime(start, "%H:%M").time()
        end_t = datetime.datetime.strptime(end, "%H:%M").time()

        obj, created = Timetable.objects.get_or_create(
            unit=unit, day=day, start_time=start_t, end_time=end_t, venue=venue
        )
        if created:
            print(f"Added {unit.code} to timetable on {day} at {venue}")

if __name__ == "__main__":
    setup_data()
