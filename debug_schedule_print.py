#!/usr/bin/env python
"""Debug script to check schedule print issue"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
sys.path.insert(0, 'c:\\Users\\User\\OneDrive\\Documents\\Auto scheduling\\ASSIST')
django.setup()

from hello.models import Faculty, Schedule
from django.contrib.auth.models import User

# Get the staff user
try:
    user = User.objects.filter(is_staff=True).first()
    if not user:
        print("No staff user found")
        sys.exit(1)
    
    faculty = Faculty.objects.get(user=user)
    schedules = Schedule.objects.filter(faculty=faculty).order_by('day', 'start_time')
    
    print(f"Faculty: {faculty.first_name} {faculty.last_name}")
    print(f"Number of schedules: {schedules.count()}")
    print("\nSchedules:")
    
    for s in schedules:
        print(f"  Day {s.day} ({['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'][s.day]}): "
              f"{s.course.course_code} {s.start_time} - {s.end_time} "
              f"(start_time type: {type(s.start_time)}, repr: {repr(s.start_time)})")
    
    # Now trace through the calculation
    print("\n\nTracing calculation for first schedule:")
    if schedules.exists():
        rs = schedules.first()
        print(f"Course: {rs.course.course_code}")
        print(f"Day: {rs.day}")
        print(f"Start time (raw): {repr(rs.start_time)}")
        print(f"End time (raw): {repr(rs.end_time)}")
        
        # Simulate normalize function
        def _normalize_time(val):
            if val is None:
                return None
            if isinstance(val, str):
                try:
                    parts = val.split(':')
                    h = int(parts[0])
                    m = int(parts[1]) if len(parts) > 1 else 0
                    return f"{h:02d}:{m:02d}"
                except Exception as e:
                    print(f"Error normalizing {val}: {e}")
                    return val
            try:
                return val.strftime('%H:%M')
            except Exception:
                return str(val)
        
        start = _normalize_time(rs.start_time)
        end = _normalize_time(rs.end_time)
        
        print(f"Start time (normalized): {repr(start)}")
        print(f"End time (normalized): {repr(end)}")
        
        # Time to minutes
        def _to_minutes(tval):
            if tval is None:
                return None
            if isinstance(tval, str):
                try:
                    parts = tval.split(':')
                    h = int(parts[0])
                    m = int(parts[1]) if len(parts) > 1 else 0
                    return h * 60 + m
                except Exception:
                    try:
                        hhmm = tval.strip().split('.')[0]
                        h, m = map(int, hhmm.split(':')[:2])
                        return h * 60 + m
                    except Exception:
                        return None
            try:
                return tval.hour * 60 + tval.minute
            except Exception:
                try:
                    s = str(tval)
                    h, m = map(int, s.split(':')[:2])
                    return h * 60 + m
                except Exception:
                    return None
        
        start_min = _to_minutes(start)
        end_min = _to_minutes(end)
        
        print(f"Start minutes: {start_min}")
        print(f"End minutes: {end_min}")
        
        base_min = 7 * 60 + 30
        print(f"Base minutes (07:30): {base_min}")
        
        start_index = (start_min - base_min) // 30
        end_index = (end_min - base_min - 1) // 30
        
        print(f"Start index: {start_index}")
        print(f"End index: {end_index}")
        
        slots = max(1, ((end_min - start_min) + 29) // 30)
        print(f"Number of slots: {slots}")
        
        # Generate time slots
        time_slots = []
        time_slots.append("07:30")
        for hour in range(8, 22):
            for minute in ['00', '30']:
                if hour == 21 and minute == '30':
                    break
                time_slots.append(f"{hour:02d}:{minute}")
        time_slots.append("21:30")
        
        print(f"\nTime slot at start_index {start_index}: {time_slots[start_index] if 0 <= start_index < len(time_slots) else 'OUT OF RANGE'}")
        print(f"Key in schedule_map: ({rs.day}, {repr(start)})")
        print(f"Lookup key in table building: ({rs.day}, {time_slots[start_index] if 0 <= start_index < len(time_slots) else 'N/A'})")

except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
