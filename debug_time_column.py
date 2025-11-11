import os
import sys
import django

# Set UTF-8 encoding for output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE','ASSIST.settings')
django.setup()

from hello.views import staff_schedule_print
from hello.models import Faculty
from django.test import RequestFactory

factory = RequestFactory()
faculty = Faculty.objects.first()
if not faculty:
    print('No faculty found')
    raise SystemExit(1)

user = faculty.user
if not user:
    print('Faculty has no user')
    raise SystemExit(1)

request = factory.get('/staff/schedule/print/')
request.user = user

resp = staff_schedule_print(request)
content = resp.content.decode()

# Extract just the time-column DIV
time_col_start = content.find('<div class="schedule-time-column"')
if time_col_start != -1:
    time_col_end = content.find('</div>', time_col_start)
    if time_col_end != -1:
        time_col_end += 6
        print("TIME COLUMN:")
        print(content[time_col_start:time_col_end][:1000])  # First 1000 chars
        print("\n... rest truncated ...\n")
        
# Extract table header and first few rows
table_start = content.find('<table class="schedule-table"')
if table_start != -1:
    # Get table opening, thead, and first 5 rows
    tbody_start = content.find('<tbody>', table_start)
    tr_count = 0
    pos = tbody_start
    while tr_count < 5 and pos < len(content):
        pos = content.find('</tr>', pos) + 5
        tr_count += 1
    
    print("TABLE HEADER AND FIRST FEW ROWS:")
    print(content[table_start:pos])
