import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','ASSIST.settings')
import django
django.setup()
from hello.models import Faculty, Schedule

# Get Stephen Nash Baldonado
fac = Faculty.objects.filter(last_name__icontains='Baldonado').first()
print(f'Faculty: {fac.first_name} {fac.last_name}')

schedules = Schedule.objects.filter(faculty=fac).select_related('course').order_by('day','start_time')

print(f'\nAll schedules for faculty:')
for s in schedules:
    print(f'  Day {s.day}: {s.start_time} to {s.end_time} = {s.course.course_code}')

# Build time slots
time_slots = []
time_slots.append("07:30")
for hour in range(8, 22):
    for minute in ['00', '30']:
        if hour == 21 and minute == '30':
            break
        time_slots.append(f"{hour:02d}:{minute}")
time_slots.append("21:30")

print(f'\nTime slots (count={len(time_slots)}):')
for i, t in enumerate(time_slots):
    print(f'  Index {i:2d}: {t}')

print(f'\nProblem: last time slot is 21:30 (index 28)')
print(f'But MATH 025 ends at 22:00, which is beyond our range!')
print(f'This causes an extended rowspan cell.')
