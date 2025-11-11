import os
import sys
import django

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault('DJANGO_SETTINGS_MODULE','ASSIST.settings')
django.setup()

from hello.views import staff_schedule_print
from hello.models import Faculty
from django.test import RequestFactory

factory = RequestFactory()
faculty = Faculty.objects.first()
user = faculty.user
request = factory.get('/staff/schedule/print/')
request.user = user

resp = staff_schedule_print(request)
content = resp.content.decode()

# Find where schedule container ends and faculty info begins
container_end = content.find('</div>  <!-- End of print-schedule-container -->')
faculty_start = content.find('<div class="faculty-info">')

if container_end != -1 and faculty_start != -1:
    print("✓ Layout is correct!")
    print(f"  Schedule container ends at position {container_end}")
    print(f"  Faculty info starts at position {faculty_start}")
    print(f"  Gap between them: {faculty_start - (container_end + 45)} chars")
    print("\nTransition section:")
    print(content[container_end:faculty_start+100])
else:
    print("✗ Structure issue detected")
    print(f"  container_end found: {container_end != -1}")
    print(f"  faculty_start found: {faculty_start != -1}")
