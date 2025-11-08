from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Sum
from datetime import datetime, timedelta
import random
import string
from .models import Course, Curriculum, Activity, Faculty, Section, Schedule, Room
from .forms import CourseForm, CurriculumForm

def admin_login(request):
    """Handle admin login with custom template"""
    if request.user.is_authenticated:
        return redirect('admin_dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_staff or user.is_superuser:
                login(request, user)
                
                if not remember_me:
                    request.session.set_expiry(0)
                
                return redirect('admin_dashboard')
            else:
                messages.error(request, 'You do not have admin privileges.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'hello/login.html')

def admin_logout(request):
    """Handle admin logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('admin_login')

@login_required
def add_schedule(request):
    """Add a new schedule entry"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Extract schedule data from POST
            section_id = request.POST.get('section')
            faculty_id = request.POST.get('faculty')
            room_id = request.POST.get('room')
            activity_id = request.POST.get('activity')
            day = request.POST.get('day')
            start_time = request.POST.get('start_time')
            duration = request.POST.get('duration')

            # Get related objects
            section = Section.objects.get(id=section_id)
            faculty = Faculty.objects.get(id=faculty_id)
            room = Room.objects.get(id=room_id)
            activity = Activity.objects.get(id=activity_id)

            # Create new schedule
            schedule = Schedule(
                section=section,
                faculty=faculty,
                room=room,
                activity=activity,
                day=day,
                start_time=start_time,
                duration=duration
            )
            
            # Validate and save
            schedule.full_clean()
            schedule.save()

            return JsonResponse({
                'success': True,
                'message': 'Schedule added successfully'
            })
            
        except (Section.DoesNotExist, Faculty.DoesNotExist, Room.DoesNotExist, Activity.DoesNotExist) as e:
            return JsonResponse({
                'success': False,
                'message': f'Required object not found: {str(e)}'
            })
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error adding schedule: {str(e)}'
            })
            
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })

@login_required(login_url='admin_login')
def admin_dashboard(request):
    """
    Admin dashboard - displays summary statistics and recent activities
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('admin_login')
    
    from django.db.models import Sum
    import json
    
    # Get counts from database
    faculty_count = Faculty.objects.count()
    section_count = Section.objects.count()
    
    # Get all curricula for forms
    curricula = Curriculum.objects.all()
    
    # Get faculty list with their total units
    faculty_list = Faculty.objects.all().order_by('last_name', 'first_name')
    
    # Get section list with schedule status
    section_list = Section.objects.all().order_by('year_level', 'semester', 'name')
    
    # Get room list for schedule creation
    room_list = Room.objects.all().order_by('campus', 'room_number')
    
    # Calculate total units for each section (counting unique courses only)
    for section in section_list:
        # Get unique course IDs for this section to avoid double-counting
        unique_course_ids = section.schedules.values_list('course', flat=True).distinct()
        
        # Sum credit units for unique courses only
        total_units = Course.objects.filter(id__in=unique_course_ids).aggregate(total=Sum('credit_units'))['total'] or 0
        section.total_units = total_units
        section.has_schedule = total_units >= 25  # Complete if 25 or more units
    
    # Get all activities from last 2 days
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    # Get activities and separate by date
    today_activities = Activity.objects.filter(
        timestamp__date=today
    ).order_by('-timestamp')[:10]

    yesterday_activities = Activity.objects.filter(
        timestamp__date=yesterday
    ).order_by('-timestamp')[:10]

    # Create recent_activities dictionary for template
    recent_activities = {}
    if today_activities:
        recent_activities['Today'] = today_activities
    if yesterday_activities:
        recent_activities['Yesterday'] = yesterday_activities
    
    # Get all courses (show all courses, not just scheduled ones)
    scheduled_courses = Course.objects.all().order_by('course_code')
    
    # Generate time slots from 7:30 AM to 9:30 PM (30-minute intervals)
    time_slots = []
    time_slots.append("07:30")
    for hour in range(8, 22):
        for minute in ['00', '30']:
            if hour == 21 and minute == '30':
                break
            time_slots.append(f"{hour:02d}:{minute}")
    time_slots.append("21:30")
    
    # Days of the week
    days = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday')
    ]
    
    # Get all schedules
    schedules = Schedule.objects.select_related(
        'course', 'section', 'faculty', 'room'
    ).all()
    
    context = {
        'user': request.user,
        'faculty_count': faculty_count,
        'section_count': section_count,
        'faculty_list': faculty_list,
        'section_list': section_list,
        'room_list': room_list,
        'recent_activities': recent_activities,
        'scheduled_courses': scheduled_courses,
        'time_slots': time_slots,
        'days': days,
        'schedules': schedules,
        'curricula': curricula,
        'all_courses': Course.objects.all().order_by('course_code'),
    }
    
    return render(request, 'hello/dashboard.html', context)

def log_activity(user, action, entity_type, entity_name, message):
    """Helper function to log activities"""
    Activity.objects.create(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_name=entity_name,
        message=message
    )

def generate_password(length=12):
    """Generate a random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choice(characters) for i in range(length))
    return password

@login_required(login_url='admin_login')
def course_view(request):
    """Course management page with filtering"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('admin_login')
    
    # Get all curricula
    curricula = Curriculum.objects.all()
    
    # Get selected filters from GET parameters
    selected_curriculum_id = request.GET.get('curriculum')
    selected_year = request.GET.get('year')
    selected_semester = request.GET.get('semester')
    
    # Get courses based on filters
    courses = Course.objects.all()
    
    selected_curriculum = None
    if selected_curriculum_id:
        selected_curriculum = get_object_or_404(Curriculum, id=selected_curriculum_id)
        courses = courses.filter(curriculum=selected_curriculum)
    elif curricula.exists():
        selected_curriculum = curricula.first()
        courses = courses.filter(curriculum=selected_curriculum)
    
    if selected_year:
        courses = courses.filter(year_level=selected_year)
    
    if selected_semester:
        courses = courses.filter(semester=selected_semester)
    
    # Group courses by year and semester
    grouped_courses = {}
    for course in courses:
        key = (course.year_level, course.semester)
        if key not in grouped_courses:
            grouped_courses[key] = {
                'display': course.get_year_semester_display(),
                'courses': [],
                'total_units': 0
            }
        grouped_courses[key]['courses'].append(course)
        grouped_courses[key]['total_units'] += course.credit_units
    
    # Academic levels for dropdown
    academic_levels = []
    for year in range(1, 5):
        for sem in range(1, 3):
            academic_levels.append({
                'year': year,
                'semester': sem,
                'display': f"{dict(Course.YEAR_CHOICES)[year]}, {dict(Course.SEMESTER_CHOICES)[sem]}"
            })
    
    context = {
        'user': request.user,
        'curricula': curricula,
        'selected_curriculum': selected_curriculum,
        'grouped_courses': grouped_courses,
        'academic_levels': academic_levels,
        'selected_year': int(selected_year) if selected_year else None,
        'selected_semester': int(selected_semester) if selected_semester else None,
    }
    return render(request, 'hello/course.html', context)

@login_required(login_url='admin_login')
def add_course(request):
    """Add new course"""
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='add',
                entity_type='course',
                entity_name=course.course_code,
                message=f'Added course: {course.course_code} - {course.descriptive_title}'
            )
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
def edit_course(request, course_id):
    """Edit existing course"""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            updated_course = form.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='edit',
                entity_type='course',
                entity_name=updated_course.course_code,
                message=f'Edited course: {updated_course.course_code} - {updated_course.descriptive_title}'
            )
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    # Return course data for editing
    course_data = {
        'id': course.id,
        'curriculum': course.curriculum.id,
        'course_code': course.course_code,
        'descriptive_title': course.descriptive_title,
        'laboratory_hours': course.laboratory_hours,
        'lecture_hours': course.lecture_hours,
        'credit_units': course.credit_units,
        'year_level': course.year_level,
        'semester': course.semester,
    }
    return JsonResponse(course_data)

@login_required(login_url='admin_login')
def delete_course(request, course_id):
    """Delete course"""
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        course_code = course.course_code
        course_title = course.descriptive_title
        
        course.delete()
        
        # Log activity
        log_activity(
            user=request.user,
            action='delete',
            entity_type='course',
            entity_name=course_code,
            message=f'Deleted course: {course_code} - {course_title}'
        )
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
def add_curriculum(request):
    """Add new curriculum"""
    if request.method == 'POST':
        form = CurriculumForm(request.POST)
        if form.is_valid():
            curriculum = form.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='add',
                entity_type='curriculum',
                entity_name=curriculum.name,
                message=f'Added curriculum: {curriculum.name} ({curriculum.year})'
            )
            
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'errors': form.errors})
    
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
def delete_curriculum(request, curriculum_id):
    """Delete curriculum"""
    if request.method == 'POST':
        curriculum = get_object_or_404(Curriculum, id=curriculum_id)
        curriculum_name = curriculum.name
        curriculum_year = curriculum.year
        
        curriculum.delete()
        
        # Log activity
        log_activity(
            user=request.user,
            action='delete',
            entity_type='curriculum',
            entity_name=curriculum_name,
            message=f'Deleted curriculum: {curriculum_name} ({curriculum_year})'
        )
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required
def edit_curriculum(request, curriculum_id):
    if request.method == 'GET':
        try:
            curriculum = Curriculum.objects.get(id=curriculum_id)
            return JsonResponse({
                'id': curriculum.id,
                'name': curriculum.name,
                'year': curriculum.year
            })
        except Curriculum.DoesNotExist:
            return JsonResponse({'error': 'Curriculum not found'}, status=404)
    
    elif request.method == 'POST':
        try:
            curriculum = Curriculum.objects.get(id=curriculum_id)
            curriculum.name = request.POST.get('name')
            curriculum.year = request.POST.get('year')
            curriculum.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='edit',
                entity_type='curriculum',
                entity_name=curriculum.name,
                message=f'Edited curriculum: {curriculum.name} ({curriculum.year})'
            )
            
            return JsonResponse({'success': True})
        except Curriculum.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Curriculum not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'errors': str(e)})
        
@login_required(login_url='admin_login')
def section_view(request):
    """Section management page"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('admin_login')
    
    # Get all sections with related data
    sections = Section.objects.select_related('curriculum').all()
    
    # Get all curricula for the add/edit form
    curricula = Curriculum.objects.all()
    
    context = {
        'user': request.user,
        'sections': sections,
        'curricula': curricula,
    }
    
    return render(request, 'hello/section.html', context)

@login_required(login_url='admin_login')
def add_section(request):
    """Add new section with validation"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            curriculum_id = request.POST.get('curriculum')
            year_level = int(request.POST.get('year_level'))
            semester = int(request.POST.get('semester'))
            max_students = int(request.POST.get('max_students', 40))
            
            section = Section(
                name=name,
                curriculum_id=curriculum_id,
                year_level=year_level,
                semester=semester,
                max_students=max_students
            )
            
            section.full_clean()
            section.save()
            
            log_activity(
                user=request.user,
                action='add',
                entity_type='section',
                entity_name=section.name,
                message=f'Added section: {section.name}'
            )
            
            return JsonResponse({'success': True})
            
        except ValidationError as e:
            error_messages = []
            if hasattr(e, 'error_dict'):
                for field, errors in e.error_dict.items():
                    for error in errors:
                        error_messages.append(error.message)
            else:
                error_messages = [str(e)]
            
            return JsonResponse({
                'success': False, 
                'errors': error_messages
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'errors': [str(e)]
            })
    
    return JsonResponse({'success': False})


@login_required(login_url='admin_login')
def edit_section(request, section_id):
    """Edit existing section with validation"""
    section = get_object_or_404(Section, id=section_id)
    
    if request.method == 'POST':
        try:
            section.name = request.POST.get('name')
            section.curriculum_id = request.POST.get('curriculum')
            section.year_level = int(request.POST.get('year_level'))
            section.semester = int(request.POST.get('semester'))
            section.max_students = int(request.POST.get('max_students'))
            
            section.full_clean()
            section.save()
            
            log_activity(
                user=request.user,
                action='edit',
                entity_type='section',
                entity_name=section.name,
                message=f'Edited section: {section.name}'
            )
            
            return JsonResponse({'success': True})
            
        except ValidationError as e:
            error_messages = []
            if hasattr(e, 'error_dict'):
                for field, errors in e.error_dict.items():
                    for error in errors:
                        error_messages.append(error.message)
            else:
                error_messages = [str(e)]
            
            return JsonResponse({
                'success': False, 
                'errors': error_messages
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'errors': [str(e)]
            })
    
    return JsonResponse({
        'id': section.id,
        'name': section.name,
        'curriculum': section.curriculum.id,
        'year_level': section.year_level,
        'semester': section.semester,
        'max_students': section.max_students,
    })

@login_required(login_url='admin_login')
def delete_section(request, section_id):
    """Delete section"""
    if request.method == 'POST':
        section = get_object_or_404(Section, id=section_id)
        section_name = section.name
        
        section.delete()
        
        log_activity(
            user=request.user,
            action='delete',
            entity_type='section',
            entity_name=section_name,
            message=f'Deleted section: {section_name}'
        )
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
def get_section_schedule(request, section_id):
    """Get schedule data for a specific section"""
    try:
        section = get_object_or_404(Section, id=section_id)
        
        print(f"\n=== Getting schedule for section: {section.name} ===")
        print(f"Curriculum: {section.curriculum.name}")
        print(f"Year Level: {section.year_level}")
        print(f"Semester: {section.semester}")
        
        # Get all schedules for this section
        schedules = Schedule.objects.filter(section=section).select_related(
            'course', 'room', 'faculty'
        ).order_by('day', 'start_time')
        
        print(f"Found {schedules.count()} schedules")
        
        # Get ALL courses for this section's curriculum, year level, and semester
        courses = Course.objects.filter(
            curriculum=section.curriculum,
            year_level=section.year_level,
            semester=section.semester
        ).order_by('course_code')
        
        print(f"Found {courses.count()} courses for this curriculum/year/semester:")
        for course in courses:
            print(f"  - {course.course_code}: {course.descriptive_title}")
        
        # Format schedule data
        schedule_data = []
        for schedule in schedules:
            schedule_item = {
                'day': schedule.day,
                'start_time': schedule.start_time,
                'end_time': schedule.end_time,
                'duration': schedule.duration,
                'course_code': schedule.course.course_code,
                'course_color': schedule.course.color,
                'room': schedule.room.name if schedule.room else 'TBA',
                'section_name': section.name,
                'faculty': f"{schedule.faculty.first_name} {schedule.faculty.last_name}" if schedule.faculty else 'TBA'
            }
            schedule_data.append(schedule_item)
        
        # Format course data
        course_data = []
        for course in courses:
            course_item = {
                'course_code': course.course_code,
                'descriptive_title': course.descriptive_title,
                'lecture_hours': course.lecture_hours,
                'laboratory_hours': course.laboratory_hours,
                'credit_units': course.credit_units,
                'color': course.color
            }
            course_data.append(course_item)
        
        return JsonResponse({
            'success': True,
            'schedules': schedule_data,
            'courses': course_data
        })
    except Exception as e:
        import traceback
        print(f"Error in get_section_schedule: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# ===== FACULTY VIEWS =====

@login_required(login_url='admin_login')
def faculty_view(request):
    """Faculty management page"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('admin_login')
    
    # Get all faculty members
    faculties = Faculty.objects.all().order_by('last_name', 'first_name')
    
    # Get all courses for specialization selection
    courses = Course.objects.all().order_by('course_code')
    
    context = {
        'user': request.user,
        'faculties': faculties,
        'courses': courses,
    }
    
    return render(request, 'hello/faculty.html', context)

@login_required(login_url='admin_login')
def add_faculty(request):
    """Add new faculty member"""
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            gender = request.POST.get('gender')
            role = request.POST.get('role')  # 'admin' or 'staff'
            employment_status = request.POST.get('employment_status')
            highest_degree = request.POST.get('highest_degree')
            prc_licensed = request.POST.get('prc_licensed') == 'on'
            specialization_ids = request.POST.getlist('specialization')
            
            # Generate random password
            password = generate_password()
            
            # Create User account
            username = f"{first_name.lower()}.{last_name.lower()}"
            base_username = username
            counter = 1
            
            # Ensure unique username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Set user permissions based on role
            if role == 'admin':
                user.is_staff = True
                user.is_superuser = True
            else:
                user.is_staff = True
                user.is_superuser = False
            
            user.save()
            
            # Create Faculty record
            faculty = Faculty.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                email=email,
                gender=gender,
                employment_status=employment_status,
                highest_degree=highest_degree,
                prc_licensed=prc_licensed
            )
            
            # Add specializations
            if specialization_ids:
                courses = Course.objects.filter(id__in=specialization_ids)
                faculty.specialization.set(courses)
            
            # Send email with credentials
            try:
                send_mail(
                    'Your ASSIST Account Credentials',
                    f'Hello {first_name},\n\n'
                    f'Your account has been created:\n\n'
                    f'Username: {username}\n'
                    f'Password: {password}\n'
                    f'Role: {role.capitalize()}\n\n'
                    f'Please login and change your password.\n\n'
                    f'Best regards,\n'
                    f'ASSIST Team',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Error sending email: {e}")
            
            # Log activity
            log_activity(
                user=request.user,
                action='add',
                entity_type='faculty',
                entity_name=f"{first_name} {last_name}",
                message=f'Added faculty: {first_name} {last_name} ({role})'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Faculty added successfully. Credentials sent to {email}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
    
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
def edit_faculty(request, faculty_id):
    """Edit existing faculty member"""
    faculty = get_object_or_404(Faculty, id=faculty_id)
    
    if request.method == 'POST':
        try:
            faculty.first_name = request.POST.get('first_name')
            faculty.last_name = request.POST.get('last_name')
            faculty.email = request.POST.get('email')
            faculty.gender = request.POST.get('gender')
            faculty.employment_status = request.POST.get('employment_status')
            faculty.highest_degree = request.POST.get('highest_degree')
            faculty.prc_licensed = request.POST.get('prc_licensed') == 'on'
            
            # Update specializations
            specialization_ids = request.POST.getlist('specialization')
            if specialization_ids:
                courses = Course.objects.filter(id__in=specialization_ids)
                faculty.specialization.set(courses)
            else:
                faculty.specialization.clear()
            
            # Update User account
            if faculty.user:
                role = request.POST.get('role')
                faculty.user.email = faculty.email
                faculty.user.first_name = faculty.first_name
                faculty.user.last_name = faculty.last_name
                
                if role == 'admin':
                    faculty.user.is_staff = True
                    faculty.user.is_superuser = True
                else:
                    faculty.user.is_staff = True
                    faculty.user.is_superuser = False
                
                faculty.user.save()
            
            faculty.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='edit',
                entity_type='faculty',
                entity_name=f"{faculty.first_name} {faculty.last_name}",
                message=f'Edited faculty: {faculty.first_name} {faculty.last_name}'
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
    
    # Return faculty data for editing
    specialization_ids = list(faculty.specialization.values_list('id', flat=True))
    role = 'admin' if faculty.user and faculty.user.is_superuser else 'staff'
    
    return JsonResponse({
        'id': faculty.id,
        'first_name': faculty.first_name,
        'last_name': faculty.last_name,
        'email': faculty.email,
        'gender': faculty.gender,
        'role': role,
        'employment_status': faculty.employment_status,
        'highest_degree': faculty.highest_degree,
        'prc_licensed': faculty.prc_licensed,
        'specialization': specialization_ids
    })

@login_required(login_url='admin_login')
def delete_faculty(request, faculty_id):
    """Delete faculty member"""
    if request.method == 'POST':
        faculty = get_object_or_404(Faculty, id=faculty_id)
        faculty_name = f"{faculty.first_name} {faculty.last_name}"
        
        # Delete associated user account
        if faculty.user:
            faculty.user.delete()
        
        faculty.delete()
        
        log_activity(
            user=request.user,
            action='delete',
            entity_type='faculty',
            entity_name=faculty_name,
            message=f'Deleted faculty: {faculty_name}'
        )
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
def get_faculty_schedule(request, faculty_id):
    """Get schedule data for a specific faculty member"""
    try:
        faculty = get_object_or_404(Faculty, id=faculty_id)
        
        # Get all schedules for this faculty
        schedules = Schedule.objects.filter(faculty=faculty).select_related(
            'course', 'section', 'room'
        ).order_by('day', 'start_time')
        
        # Format schedule data
        schedule_data = []
        for schedule in schedules:
            schedule_item = {
                'day': schedule.day,
                'start_time': schedule.start_time,
                'end_time': schedule.end_time,
                'duration': schedule.duration,
                'course_code': schedule.course.course_code,
                'course_title': schedule.course.descriptive_title,
                'course_color': schedule.course.color,
                'room': schedule.room.name if schedule.room else 'TBA',
                'section_name': schedule.section.name,
            }
            schedule_data.append(schedule_item)
        
        # Get faculty specializations
        specializations = []
        for course in faculty.specialization.all():
            specializations.append({
                'course_code': course.course_code,
                'descriptive_title': course.descriptive_title,
                'color': course.color
            })
        
        return JsonResponse({
            'success': True,
            'schedules': schedule_data,
            'specializations': specializations,
            'total_units': faculty.total_units
        })
    except Exception as e:
        import traceback
        print(f"Error in get_faculty_schedule: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    
    # ===== ROOM VIEWS =====

@login_required(login_url='admin_login')
def room_view(request):
    """Room management page"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('admin_login')
    
    # Get all rooms
    rooms = Room.objects.all().order_by('campus', 'room_number')
    
    context = {
        'user': request.user,
        'rooms': rooms,
    }
    
    return render(request, 'hello/room.html', context)

@login_required(login_url='admin_login')
def add_room(request):
    """Add new room"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            room_number = request.POST.get('room_number')
            capacity = int(request.POST.get('capacity', 40))
            campus = request.POST.get('campus')
            room_type = request.POST.get('room_type')
            
            room = Room.objects.create(
                name=name,
                room_number=room_number,
                capacity=capacity,
                campus=campus,
                room_type=room_type
            )
            
            log_activity(
                user=request.user,
                action='add',
                entity_type='room',
                entity_name=room.name,
                message=f'Added room: {room.name} - {room.get_campus_display()} Campus'
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
    
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
def edit_room(request, room_id):
    """Edit existing room"""
    room = get_object_or_404(Room, id=room_id)
    
    if request.method == 'POST':
        try:
            room.name = request.POST.get('name')
            room.room_number = request.POST.get('room_number')
            room.capacity = int(request.POST.get('capacity'))
            room.campus = request.POST.get('campus')
            room.room_type = request.POST.get('room_type')
            
            room.save()
            
            log_activity(
                user=request.user,
                action='edit',
                entity_type='room',
                entity_name=room.name,
                message=f'Edited room: {room.name} - {room.get_campus_display()} Campus'
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
    
    return JsonResponse({
        'id': room.id,
        'name': room.name,
        'room_number': room.room_number,
        'capacity': room.capacity,
        'campus': room.campus,
        'room_type': room.room_type,
    })

@login_required(login_url='admin_login')
def delete_room(request, room_id):
    """Delete room"""
    if request.method == 'POST':
        room = get_object_or_404(Room, id=room_id)
        room_name = room.name
        
        room.delete()
        
        log_activity(
            user=request.user,
            action='delete',
            entity_type='room',
            entity_name=room_name,
            message=f'Deleted room: {room_name}'
        )
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
def get_room_schedule(request, room_id):
    """Get schedule data for a specific room"""
    try:
        room = get_object_or_404(Room, id=room_id)
        
        # Get all schedules for this room
        schedules = Schedule.objects.filter(room=room).select_related(
            'course', 'section', 'faculty'
        ).order_by('day', 'start_time')
        
        # Format schedule data
        schedule_data = []
        courses_map = {}
        
        for schedule in schedules:
            schedule_item = {
                'day': schedule.day,
                'start_time': schedule.start_time,
                'end_time': schedule.end_time,
                'duration': schedule.duration,
                'course_code': schedule.course.course_code,
                'course_title': schedule.course.descriptive_title,
                'course_color': schedule.course.color,
                'section_name': schedule.section.name,
                'faculty': f"{schedule.faculty.first_name} {schedule.faculty.last_name}" if schedule.faculty else 'TBA',
                # Add room information for display
                'room_name': room.name,
                'room_number': room.room_number,
                'campus': room.campus
            }
            schedule_data.append(schedule_item)
            
            # Track unique courses for sidebar
            if schedule.course.course_code not in courses_map:
                courses_map[schedule.course.course_code] = {
                    'course_code': schedule.course.course_code,
                    'descriptive_title': schedule.course.descriptive_title,
                    'color': schedule.course.color,
                    'lecture_hours': schedule.course.lecture_hours,
                    'laboratory_hours': schedule.course.laboratory_hours,
                    'credit_units': schedule.course.credit_units
                }
        
        # Convert courses_map to list
        courses_list = list(courses_map.values())
        
        return JsonResponse({
            'success': True,
            'schedules': schedule_data,
            'courses': courses_list,
            'room_info': {
                'name': room.name,
                'room_number': room.room_number,
                'campus': room.get_campus_display(),
                'room_type': room.get_room_type_display(),
                'capacity': room.capacity
            }
        })
    except Exception as e:
        import traceback
        print(f"Error in get_room_schedule: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)