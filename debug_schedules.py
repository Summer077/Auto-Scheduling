#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from hello.models import Schedule, Faculty

# Get schedules organized by time
all_schedules = Schedule.objects.select_related('course', 'faculty', 'section').order_by('day', 'start_time')

print('=== ALL SCHEDULES BY TIME ===\n')

princess = Faculty.objects.get(first_name__icontains='Princess')

by_time = {}
for s in all_schedules:
    key = f"Day {s.day} {s.start_time}-{s.end_time}"
    if key not in by_time:
        by_time[key] = []
    by_time[key].append(s)

for time_slot in sorted(by_time.keys()):
    schedules_at_this_time = by_time[time_slot]
    print(f'{time_slot}:')
    for s in schedules_at_this_time:
        fac = s.faculty.full_name if s.faculty else 'UNASSIGNED'
        marker = ' <-- PRINCESS' if s.faculty_id == princess.id else ''
        print(f'  {s.course.course_code} ({s.section.name}) - {fac}{marker}')
    print()
