import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE','ASSIST.settings')
django.setup()

from hello.models import Section
from hello.views import get_section_schedule
from django.test import RequestFactory
from django.contrib.auth import get_user_model

section = Section.objects.filter(name='CPE11S1').first()
if not section:
    print('Section CPE11S1 not found')
    raise SystemExit(1)

factory = RequestFactory()
request = factory.get(f'/admin/section/{section.id}/schedule-data/')
request.user = get_user_model().objects.filter(is_staff=True).first()

resp = get_section_schedule(request, section.id)
print(resp.content.decode())
