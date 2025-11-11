#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from django.contrib.auth.models import User
from hello.models import Faculty, Schedule

user = User.objects.get(username='princess.mariano')
faculty = Faculty.objects.get(user=user)

schedules = Schedule.objects.filter(faculty=faculty).select_related(
    'course', 'section', 'room'
).order_by('day', 'start_time')

print(f'Schedules passed to Princess dashboard template: {schedules.count()}')
print()

for schedule in schedules:
    print(f'{schedule.course.course_code} - {schedule.section.name} (Day {schedule.day})')
