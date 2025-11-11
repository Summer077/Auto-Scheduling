import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','ASSIST.settings')
import django
django.setup()
from hello.models import Faculty, Schedule, Course
from datetime import datetime

# Get Stephen Nash Baldonado
fac = Faculty.objects.filter(last_name__icontains='Baldonado').first()
print('Faculty:', fac and (fac.id, fac.first_name, fac.last_name) or 'Not found')

schedules = Schedule.objects.filter(faculty=fac).select_related('course','section').order_by('day','start_time')
print(f'\nSchedules count: {schedules.count()}')

# Build time slots
time_slots = []
time_slots.append("07:30")
for hour in range(8, 22):
    for minute in ['00', '30']:
        if hour == 21 and minute == '30':
            break
        time_slots.append(f"{hour:02d}:{minute}")
time_slots.append("21:30")

print(f'Time slots count: {len(time_slots)}')
print(f'Time slots: {time_slots}')

# Helper functions
def _normalize_time(val):
    if val is None:
        return None
    if isinstance(val, str):
        try:
            parts = val.split(':')
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 0
            return f"{h:02d}:{m:02d}"
        except Exception:
            return val
    try:
        return val.strftime('%H:%M')
    except Exception:
        return str(val)

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

# Build schedule map
raw_schedules = []
for schedule in schedules:
    raw_schedules.append({
        'day': schedule.day,
        'start_time': schedule.start_time,
        'end_time': schedule.end_time,
        'course_code': schedule.course.course_code,
        'room': schedule.room.name if schedule.room else 'TBA',
    })

schedule_map = {}
covered = set()

for rs in raw_schedules:
    day_idx = rs['day']
    start = _normalize_time(rs['start_time'])
    end = _normalize_time(rs['end_time'])
    
    start_min = _to_minutes(start)
    end_min = _to_minutes(end)
    
    base_min = 7 * 60 + 30
    start_index = (start_min - base_min) // 30
    end_index = (end_min - base_min) // 30
    
    start_index = max(0, start_index)
    end_index = max(start_index, min(len(time_slots) - 1, end_index))
    
    slots = max(1, end_index - start_index + 1)
    key = (day_idx, start)
    
    print(f'\nSchedule: {rs["course_code"]} on day {day_idx} from {start} to {end}')
    print(f'  Minutes: {start_min} to {end_min}')
    print(f'  Indices: {start_index} to {end_index} (slots={slots})')
    print(f'  Map key: {key}')
    
    schedule_map[key] = {
        'rowspan': slots,
        'course_code': rs['course_code'],
        'room': rs['room'],
    }
    
    for j in range(1, slots):
        idx = start_index + j
        if idx < len(time_slots):
            covered_key = (day_idx, time_slots[idx])
            covered.add(covered_key)
            print(f'    Marked covered: ({day_idx}, {time_slots[idx]})')

print(f'\nSchedule map entries: {len(schedule_map)}')
print(f'Covered slots: {len(covered)}')

# Build table rows
table_rows = []
for t in time_slots:
    cells = []
    for d in range(6):
        if (d, t) in covered:
            cells.append('skip')
        elif (d, t) in schedule_map:
            cells.append('ENTRY')
        else:
            cells.append(None)
    table_rows.append({'time': t, 'cells': cells})

# Look for rows with issues
print('\n--- Row-by-row analysis ---')
for i, row in enumerate(table_rows):
    cells = row['cells']
    if 'ENTRY' in cells or 'skip' in cells:
        print(f"Row {i:2d} {row['time']}: {cells}")
