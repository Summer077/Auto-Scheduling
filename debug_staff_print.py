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
from django.contrib.auth import get_user_model

factory = RequestFactory()
# pick a faculty that exists
faculty = Faculty.objects.first()
if not faculty:
    print('No faculty found')
    raise SystemExit(1)

# pick the associated user
user = faculty.user
if not user:
    print('Faculty has no user')
    raise SystemExit(1)

request = factory.get('/staff/schedule/print/')
request.user = user

resp = staff_schedule_print(request)
# Print the schedule container (includes time-column DIV + table)
content = resp.content.decode()
start = content.find('<div class="print-schedule-container"')
if start != -1:
    # Find the matching closing </div> by counting nested divs
    div_count = 1
    pos = start + len('<div class="print-schedule-container"')
    while div_count > 0 and pos < len(content):
        next_open = content.find('<div', pos)
        next_close = content.find('</div>', pos)
        
        if next_close == -1:
            break
        if next_open != -1 and next_open < next_close:
            div_count += 1
            pos = next_open + 4
        else:
            div_count -= 1
            if div_count == 0:
                end = next_close + 6
                print(content[start:end])
                break
            pos = next_close + 6
