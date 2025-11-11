import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','ASSIST.settings')
import django
django.setup()
from hello.models import Faculty, Schedule

# Get Stephen Nash Baldonado
fac = Faculty.objects.filter(last_name__icontains='Baldonado').first()
if not fac:
    print("Faculty not found")
    exit(1)

print(f'Faculty: {fac.first_name} {fac.last_name}')
print(f'\n=== DATABASE SCHEDULES ===')

schedules = Schedule.objects.filter(faculty=fac).select_related('course').order_by('day', 'start_time')
day_names = ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']

for s in schedules:
    print(f'{day_names[s.day]:10s} {s.start_time:5s} - {s.end_time:5s}: {s.course.course_code:10s} Room: {s.room.name if s.room else "TBA"}')

print(f'\nTotal schedules in database: {schedules.count()}')
print('\n=== WHAT APPEARS IN PRINT TABLE ===')
print('(Open http://127.0.0.1:8000/staff/schedule/print/ and check which courses appear in each time slot)')
print('If something is missing or different, please note which day/time and which course.')
