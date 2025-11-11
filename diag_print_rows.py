import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','ASSIST.settings')
import django
django.setup()
from hello.models import Faculty, Schedule

fac = Faculty.objects.filter(last_name__icontains='Baldonado').first()
if not fac:
    print('Faculty not found')
    exit(1)

schedules = Schedule.objects.filter(faculty=fac).select_related('course','section','room').order_by('day','start_time')

raw_schedules = []
for schedule in schedules:
    if schedule.faculty_id != fac.id:
        continue
    raw_schedules.append({
        'day': schedule.day,
        'start_time': schedule.start_time,
        'end_time': schedule.end_time,
        'course_code': schedule.course.course_code,
        'room': schedule.room.name if schedule.room else 'TBA',
        'section_name': schedule.section.name,
    })

# time_slots
time_slots = []
time_slots.append('07:30')
for hour in range(8,22):
    for minute in ['00','30']:
        if hour == 21 and minute == '30':
            break
        time_slots.append(f"{hour:02d}:{minute}")
time_slots.append('21:30')

days = ['MON','TUE','WED','THU','FRI','SAT']

# helpers
from datetime import time as _time

def _normalize_time(val):
    if val is None: return None
    if isinstance(val, str):
        try:
            parts = val.split(':')
            h = int(parts[0]); m = int(parts[1]) if len(parts)>1 else 0
            return f"{h:02d}:{m:02d}"
        except: return val
    try: return val.strftime('%H:%M')
    except: return str(val)

def _to_minutes(tval):
    if tval is None: return None
    if isinstance(tval,str):
        try:
            parts = tval.split(':'); h=int(parts[0]); m=int(parts[1]) if len(parts)>1 else 0
            return h*60+m
        except:
            try:
                hhmm = tval.strip().split('.')[0]
                h,m = map(int, hhmm.split(':')[:2]); return h*60+m
            except: return None
    try: return tval.hour*60 + tval.minute
    except:
        try:
            s=str(tval); h,m = map(int,s.split(':')[:2]); return h*60+m
        except: return None

schedule_map = {}
covered = set()

for rs in raw_schedules:
    day_idx = rs['day']
    start = _normalize_time(rs['start_time'])
    end = _normalize_time(rs['end_time'])
    if not start or not end:
        key=(day_idx,start)
        schedule_map[key] = {'rowspan':1,'course_code':rs['course_code'],'room':rs['room']}
        continue
    start_min = _to_minutes(start); end_min = _to_minutes(end)
    if start_min is None or end_min is None:
        key=(day_idx,start)
        schedule_map[key] = {'rowspan':1,'course_code':rs['course_code'],'room':rs['room']}
        continue
    base_min = 7*60+30
    start_index = (start_min - base_min)//30
    # See views.py fix: subtract 1 minute so end times on slot boundaries don't include the next slot
    end_index = (end_min - base_min - 1)//30
    start_index = max(0, start_index)
    end_index = max(start_index, min(len(time_slots)-1, end_index))
    slots = max(1, end_index - start_index + 1)
    key=(day_idx,start)
    schedule_map[key] = {'rowspan':slots,'course_code':rs['course_code'],'room':rs['room']}
    for j in range(1, slots):
        idx = start_index + j
        if idx < len(time_slots):
            covered.add((day_idx, time_slots[idx]))

# Build table_rows (current logic uses 'skip')
table_rows = []
for t in time_slots:
    cells=[]
    for d in range(6):
        if (d,t) in covered:
            cells.append('skip')
        elif (d,t) in schedule_map:
            cells.append(schedule_map[(d,t)])
        else:
            cells.append(None)
    table_rows.append({'time':t,'cells':cells})

# print rows from 14:00 index 13 to end
start_idx = time_slots.index('14:00')
print('Time slots:', time_slots[start_idx:])
for i in range(start_idx, len(time_slots)):
    row = table_rows[i]
    print(row['time'], ['S' if (c=='skip') else (c['course_code'] if isinstance(c,dict) else None) for c in row['cells']])

print('\nSchedule map keys:')
for k,v in schedule_map.items():
    print(k, v)

print('\nCovered sample (sorted):')
print(sorted(list(covered)))
