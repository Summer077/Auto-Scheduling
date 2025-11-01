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
def admin_dashboard(request):
    """
    Admin dashboard - displays summary statistics and recent activities
    Fetches data directly from Django database
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('admin_login')
    
    # Get counts from database
    faculty_count = Faculty.objects.count()
    section_count = Section.objects.count()
    
    # Get recent activities (last 2 days)
    recent_activities = get_recent_activities()
    
    # Get courses that have schedules assigned
    scheduled_courses = Course.objects.filter(schedules__isnull=False).distinct()
    
    # Generate time slots from 7:30 AM to 9:30 PM
    time_slots = generate_time_slots()
    
    # Days of the week
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    # Get schedules
    schedules = Schedule.objects.all().select_related('course', 'section', 'room', 'faculty')
    
    context = {
        'user': request.user,
        'faculty_count': faculty_count,
        'section_count': section_count,
        'recent_activities': recent_activities,
        'scheduled_courses': scheduled_courses,
        'time_slots': time_slots,
        'days': days,
        'schedules': schedules,
    }
    
    return render(request, 'hello/dashboard.html', context)

def generate_time_slots():
    """Generate time slots from 7:30 AM to 9:30 PM in 30-minute intervals"""
    time_slots = []
    current_hour = 7
    current_minute = 30
    
    while current_hour < 21 or (current_hour == 21 and current_minute == 0):
        time_str = f"{current_hour}:{current_minute:02d}"
        time_slots.append(time_str)
        
        # Increment by 30 minutes
        current_minute += 30
        if current_minute >= 60:
            current_minute = 0
            current_hour += 1
    
    # Add final 9:30 PM slot
    time_slots.append("21:30")
    
    return time_slots

def get_recent_activities():
    """
    Get recent activities grouped by day (Today, Yesterday)
    Returns activities from Activity model
    """
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    activities_dict = {}
    
    # Get activities from today
    today_activities = Activity.objects.filter(
        timestamp__date=today
    ).order_by('-timestamp')
    
    if today_activities.exists():
        activities_dict['Today'] = list(today_activities)
    
    # Get activities from yesterday
    yesterday_activities = Activity.objects.filter(
        timestamp__date=yesterday
    ).order_by('-timestamp')
    
    if yesterday_activities.exists():
        activities_dict['Yesterday'] = list(yesterday_activities)
    
    return activities_dict

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
    return render(request, 'hello/course_management.html', context)

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
            course = form.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='edit',
                entity_type='course',
                entity_name=course.course_code,
                message=f'Edited course: {course.course_code} - {course.descriptive_title}'
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
                entity_name=f'{curriculum.name} ({curriculum.year})',
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
        curriculum_name = f'{curriculum.name} ({curriculum.year})'
        
        curriculum.delete()
        
        # Log activity
        log_activity(
            user=request.user,
            action='delete',
            entity_type='curriculum',
            entity_name=curriculum_name,
            message=f'Deleted curriculum: {curriculum_name}'
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
            old_name = f'{curriculum.name} ({curriculum.year})'
            
            curriculum.name = request.POST.get('name')
            curriculum.year = request.POST.get('year')
            curriculum.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='edit',
                entity_type='curriculum',
                entity_name=f'{curriculum.name} ({curriculum.year})',
                message=f'Edited curriculum: {old_name} → {curriculum.name} ({curriculum.year})'
            )
            
            return JsonResponse({'success': True})
        except Curriculum.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Curriculum not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'errors': str(e)})