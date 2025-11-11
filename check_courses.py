#!/usr/bin/env python
"""Check course end times in database"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ASSIST.settings')
sys.path.insert(0, 'c:\\Users\\User\\OneDrive\\Documents\\Auto scheduling\\ASSIST')
django.setup()

from hello.models import Schedule
from django.contrib.auth.models import User

# Get staff user
user = User.objects.filter(is_staff=True).first()
if user:
    from hello.models import Faculty
    try:
        faculty = Faculty.objects.get(user=user)
        schedules = Schedule.objects.filter(faculty=faculty).order_by('day', 'start_time')
        
        print("=" * 70)
        print(f"Faculty: {faculty.first_name} {faculty.last_name}")
        print("=" * 70)
        print(f"{'Course':<15} {'Day':<12} {'Start':<10} {'End':<10} {'Duration':<10}")
        print("-" * 70)
        
        for s in schedules:
            day_name = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'][s.day]
            
            # Parse times
            start_h, start_m = map(int, s.start_time.split(':'))
            end_h, end_m = map(int, s.end_time.split(':'))
            
            start_min = start_h * 60 + start_m
            end_min = end_h * 60 + end_m
            duration_min = end_min - start_min
            duration_hrs = duration_min / 60
            
            print(f"{s.course.course_code:<15} {day_name:<12} {s.start_time:<10} {s.end_time:<10} {duration_hrs}h")
        
        print("-" * 70)
        print(f"Total schedules: {schedules.count()}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
else:
    print("No staff user found")
