#!/usr/bin/env python
"""
Test script to verify staff_schedule.html renders correctly with Stephen Nash's data
"""
import os
import django
import json
from django.template.loader import render_to_string

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
django.setup()

from django.contrib.auth.models import User
from hello.models import Faculty, Schedule

# Get Stephen Nash's data
u = User.objects.get(username='stephennash.baldonado')
f = Faculty.objects.get(user=u)
schedules = Schedule.objects.filter(faculty=f).select_related('course', 'section', 'room').order_by('day', 'start_time')

# Build schedule_data exactly as the view does
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

# Create context exactly as the view does
context = {
    'user': u,
    'faculty': f,
    'schedules': json.dumps(schedule_data),
    'time_slots': [],
    'days': [],
    'specializations': f.specialization.all(),
}

# Try to render the template
try:
    html = render_to_string('hello/staff_schedule.html', context)
    
    # Check if renderStaffSchedule is called
    if 'renderStaffSchedule(scheduleData)' in html:
        print("✓ Template includes renderStaffSchedule call")
    else:
        print("✗ Template missing renderStaffSchedule call")
    
    # Check if scheduleData is properly set
    if '"day": 0' in html or "'day': 0" in html:
        print("✓ Schedule data is present in rendered HTML")
    else:
        print("✗ Schedule data is missing from rendered HTML")
    
    # Check if account_settings is NOT inside script tag
    if '<script>\n    {% include' in html or '<script>\n    <' not in html:
        print("✓ Account settings NOT inside script tag")
    else:
        print("⚠ Need to verify account_settings placement")
    
    # Write rendered HTML to file for inspection
    with open('test_rendered_staff_schedule.html', 'w') as f:
        f.write(html)
    print("\n✓ Rendered template saved to test_rendered_staff_schedule.html")
    
    # Extract and print the schedule data section
    import re
    schedule_match = re.search(r'const scheduleData = (\[.*?\]);', html, re.DOTALL)
    if schedule_match:
        data = schedule_match.group(1)
        schedules_in_template = json.loads(data)
        print(f"\n✓ Found {len(schedules_in_template)} schedules in rendered template")
        print(f"  First schedule: {schedules_in_template[0]['course_code']} on day {schedules_in_template[0]['day']}")
    else:
        print("\n✗ Could not extract scheduleData from template")
    
except Exception as e:
    print(f"✗ Error rendering template: {e}")
    import traceback
    traceback.print_exc()
