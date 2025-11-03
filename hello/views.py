from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Course, Curriculum, Activity, Faculty, Section, Schedule
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

@login_required(login_url='admin_login')
def admin_dashboard(request):
    """
    Admin dashboard - displays summary statistics and recent activities
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('admin_login')
    
    # Get counts from database
    faculty_count = Faculty.objects.count()
    section_count = Section.objects.count()
    
    # Get faculty list with their total units
    faculty_list = Faculty.objects.all().order_by('last_name', 'first_name')
    
    # Get section list with schedule status
    section_list = Section.objects.all().order_by('year_level', 'semester', 'name')
    # Calculate total units for each section and check if schedule is complete (25 units)
    for section in section_list:
        # Get all schedules for this section and sum up the credit units
        total_units = 0
        schedules = section.schedules.select_related('course').all()
        for schedule in schedules:
            total_units += schedule.course.credit_units
        
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
    # Start at 7:30
    time_slots.append("07:30")
    # Then 8:00 onwards
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
        'recent_activities': recent_activities,
        'scheduled_courses': scheduled_courses,
        'time_slots': time_slots,
        'days': days,
        'schedules': schedules,
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