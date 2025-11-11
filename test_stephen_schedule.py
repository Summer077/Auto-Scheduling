#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from django.contrib.auth.models import User
from hello.models import Faculty, Schedule
import json

u = User.objects.get(username='stephennash.baldonado')
f = Faculty.objects.get(user=u)
schedules = Schedule.objects.filter(faculty=f).select_related('course', 'section', 'room').order_by('day', 'start_time')

schedule_data = []
for schedule in schedules:
    if schedule.faculty_id != f.id:
        continue
    schedule_data.append({
        'day': schedule.day,
        'start_time': str(schedule.start_time),
        'end_time': str(schedule.end_time),
        'duration': schedule.duration,
        'course_code': schedule.course.course_code,
        'course_title': schedule.course.descriptive_title,
        'course_color': schedule.course.color,
        'room': schedule.room.name if schedule.room else 'TBA',
        'section_name': schedule.section.name,
    })

print("Schedule data for Stephen Nash (all):")
print(json.dumps(schedule_data, indent=2))
print(f"\nTotal schedules: {len(schedule_data)}")
