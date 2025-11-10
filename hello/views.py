from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.db.models import Sum
from datetime import datetime, timedelta
import random
import string
from .models import Course, Curriculum, Activity, Faculty, Section, Schedule, Room
from .forms import CourseForm, CurriculumForm

# Helper function to check if user is admin
def is_admin(user):
    return user.is_staff and user.is_superuser

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
                
                # Redirect based on user role
                if user.is_superuser:
                    return redirect('admin_dashboard')
                else:
                    return redirect('staff_dashboard')  # Create this view for staff
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
    if request.method == 'POST':
        try:
            # Extract schedule data from POST
            course_id = request.POST.get('course')
            section_id = request.POST.get('section')
            faculty_id = request.POST.get('faculty')
            room_id = request.POST.get('room')
            day = request.POST.get('day')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')

            # Get related objects
            course = Course.objects.get(id=course_id)
            section = Section.objects.get(id=section_id)
            faculty = Faculty.objects.get(id=faculty_id) if faculty_id else None
            room = Room.objects.get(id=room_id) if room_id else None

            # Create new schedule
            schedule = Schedule(
                course=course,
                section=section,
                faculty=faculty,
                room=room,
                day=int(day),
                start_time=start_time,
                end_time=end_time
            )
            
            # Validate and save (duration will be calculated automatically in save method)
            schedule.full_clean()
            schedule.save()

            # Log activity
            log_activity(
                user=request.user,
                action='add',
                entity_type='schedule',
                entity_name=f"{course.course_code} - {section.name}",
                message=f'Created schedule: {course.course_code} for {section.name} on {dict(Schedule.DAY_CHOICES)[int(day)]}'
            )

            return JsonResponse({
                'success': True,
                'message': 'Schedule created successfully'
            })
            
        except Course.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Course not found']
            })
        except Section.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Section not found']
            })
        except Faculty.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Faculty not found']
            })
        except Room.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Room not found']
            })
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
            import traceback
            print(f"Error creating schedule: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [f'Error creating schedule: {str(e)}']
            })
            
    return JsonResponse({
        'success': False,
        'errors': ['Invalid request method']
    })

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def admin_dashboard(request):
    """
    Admin dashboard - displays summary statistics and recent activities
    ONLY accessible by superusers (admins)
    """
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
        calculated_units = Course.objects.filter(id__in=unique_course_ids).aggregate(total=Sum('credit_units'))['total'] or 0
        
        # Add as a temporary attribute (not the property)
        section.calculated_total_units = calculated_units
        
        # Use the actual status field from the database
        section.has_schedule = (section.status == 'complete')
    
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
    """Generate a random password with at least one uppercase, lowercase, digit, and special character"""
    # Ensure password has at least one of each required type
    password_chars = [
        random.choice(string.ascii_uppercase),
        random.choice(string.ascii_lowercase),
        random.choice(string.digits),
        random.choice("!@#$%^&*")
    ]
    
    # Fill the rest with random characters
    all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password_chars += [random.choice(all_chars) for _ in range(length - 4)]
    
    # Shuffle to avoid predictable pattern
    random.shuffle(password_chars)
    return ''.join(password_chars)

# ===== FACULTY VIEWS =====

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def faculty_view(request):
    """Faculty management page"""
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
@user_passes_test(is_admin, login_url='admin_login')
def add_faculty(request):
    """Add new faculty member with proper email validation and sending"""
    if request.method == 'POST':
        try:
            # Get form data
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            gender = request.POST.get('gender')
            role = request.POST.get('role')
            employment_status = request.POST.get('employment_status')
            highest_degree = request.POST.get('highest_degree', '')
            prc_licensed = request.POST.get('prc_licensed') == 'on'
            specialization_ids = request.POST.getlist('specialization')
            
            # Validate email domain
            if '@' not in email or '.' not in email.split('@')[1]:
                return JsonResponse({
                    'success': False,
                    'errors': ['Please enter a valid email address with a proper domain (e.g., user@gmail.com)']
                })
            
            # Check if email already exists
            if Faculty.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['This email is already registered.']
                })
            
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
            
            # Check if email already used by another user
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['This email is already associated with another account.']
                })
            
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
            
            # Send email with credentials using EmailMessage for better control
            try:
                subject = 'Your ASSIST Account Credentials'
                message = f'''Hello {first_name},

Your account has been created successfully for the ASSIST system.

Login Credentials:
------------------
Username: {username}
Password: {password}
Role: {role.capitalize()}

Please login to the system and change your password immediately for security purposes.

If you did not request this account, please contact the administrator.

Best regards,
ASSIST Administration Team'''

                email_message = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email],
                )
                
                email_message.send(fail_silently=False)
                
                email_sent = True
                message_text = f'Faculty added successfully. Credentials have been sent to {email}'
                
            except Exception as e:
                print(f"Error sending email: {str(e)}")
                email_sent = False
                message_text = f'Faculty added successfully, but email could not be sent. Please provide credentials manually:\nUsername: {username}\nPassword: {password}'
            
            # Log activity
            log_activity(
                user=request.user,
                action='add',
                entity_type='faculty',
                entity_name=f"{first_name} {last_name}",
                message=f'Added faculty: {first_name} {last_name} ({role}) - Email {"sent" if email_sent else "failed"}'
            )
            
            return JsonResponse({
                'success': True,
                'message': message_text,
                'credentials': {
                    'username': username,
                    'password': password
                } if not email_sent else None
            })
            
        except Exception as e:
            import traceback
            print(f"Error adding faculty: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [f'Error adding faculty: {str(e)}']
            })
    
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_faculty(request, faculty_id):
    """Edit existing faculty member"""
    faculty = get_object_or_404(Faculty, id=faculty_id)
    
    if request.method == 'POST':
        try:
            email = request.POST.get('email')
            
            # Validate email domain
            if '@' not in email or '.' not in email.split('@')[1]:
                return JsonResponse({
                    'success': False,
                    'errors': ['Please enter a valid email address with a proper domain (e.g., user@gmail.com)']
                })
            
            # Check if email is taken by another faculty
            if Faculty.objects.filter(email=email).exclude(id=faculty_id).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['This email is already registered to another faculty member.']
                })
            
            faculty.first_name = request.POST.get('first_name')
            faculty.last_name = request.POST.get('last_name')
            faculty.email = email
            faculty.gender = request.POST.get('gender')
            faculty.employment_status = request.POST.get('employment_status')
            faculty.highest_degree = request.POST.get('highest_degree', '')
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
@user_passes_test(is_admin, login_url='admin_login')
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
    
@login_required(login_url='admin_login')
def schedule_view(request):
    """Schedule management page - shows sections"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('admin_login')
    
    # Get all sections with their schedules
    sections = Section.objects.select_related('curriculum').all()
    
    # Calculate total units for each section
    for section in sections:
        unique_course_ids = section.schedules.values_list('course', flat=True).distinct()
        total = Course.objects.filter(id__in=unique_course_ids).aggregate(
            total=Sum('credit_units')
        )['total'] or 0
        section.calculated_total_units = total
    
    # Get data needed for the create schedule modal
    all_courses = Course.objects.all().order_by('course_code')
    faculty_list = Faculty.objects.all().order_by('last_name', 'first_name')
    section_list = Section.objects.all().order_by('year_level', 'semester', 'name')
    room_list = Room.objects.all().order_by('campus', 'room_number')
    
    context = {
        'user': request.user,
        'sections': sections,
        'all_courses': all_courses,
        'faculty_list': faculty_list,
        'section_list': section_list,
        'room_list': room_list,
    }
    
    return render(request, 'hello/schedule.html', context)

@login_required(login_url='admin_login')
def toggle_section_status(request, section_id):
    """Toggle section schedule status"""
    if request.method == 'POST':
        section = get_object_or_404(Section, id=section_id)
        
        # Toggle status
        if section.status == 'complete':
            section.status = 'incomplete'
            status_text = 'No Schedule Yet'
        else:
            section.status = 'complete'
            status_text = 'Complete Schedule'
        
        section.save()
        
        log_activity(
            user=request.user,
            action='edit',
            entity_type='section',
            entity_name=section.name,
            message=f'Updated schedule status for {section.name} to: {status_text}'
        )
        
        return JsonResponse({
            'success': True,
            'status': section.status,
            'status_display': section.get_status_display()
        })
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
def delete_schedule(request, schedule_id):
    """Delete schedule"""
    if request.method == 'POST':
        schedule = get_object_or_404(Schedule, id=schedule_id)
        course_code = schedule.course.course_code
        section_name = schedule.section.name
        
        schedule.delete()
        
        log_activity(
            user=request.user,
            action='delete',
            entity_type='schedule',
            entity_name=f"{course_code} - {section_name}",
            message=f'Deleted schedule: {course_code} for {section_name}'
        )
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
def staff_dashboard(request):
    """
    Staff dashboard - limited view for non-admin faculty
    Shows their schedule and basic information
    """
    # Check if user has faculty profile
    try:
        faculty = Faculty.objects.get(user=request.user)
    except Faculty.DoesNotExist:
        messages.error(request, 'No faculty profile found for your account.')
        logout(request)
        return redirect('admin_login')
    
    # Get faculty's schedules
    schedules = Schedule.objects.filter(faculty=faculty).select_related(
        'course', 'section', 'room'
    ).order_by('day', 'start_time')
    
    # Generate time slots
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
    
    # Get specializations
    specializations = faculty.specialization.all()
    
    context = {
        'user': request.user,
        'faculty': faculty,
        'schedules': schedules,
        'time_slots': time_slots,
        'days': days,
        'specializations': specializations,
    }
    
    return render(request, 'hello/staff_dashboard.html', context)