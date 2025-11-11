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
from django.db.models import Sum, Q
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
    # If user is already authenticated, redirect based on role
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        elif request.user.is_staff:
            return redirect('staff_dashboard')
        else:
            # Regular user - logout and show error
            logout(request)
            messages.error(request, 'You do not have admin privileges.')
            return render(request, 'hello/login.html')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if user has staff privileges
            if user.is_staff:
                login(request, user)
                
                # Set session expiry
                if not remember_me:
                    request.session.set_expiry(0)
                
                # Redirect based on user role
                if user.is_superuser:
                    return redirect('admin_dashboard')
                else:
                    return redirect('staff_dashboard')
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
    """Add a new schedule entry with conflict detection"""
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

            # Check for conflicts
            conflicts = []
            warnings = []
            
            # Check section conflict (same section, same day, overlapping time)
            section_conflicts = Schedule.objects.filter(
                section=section,
                day=int(day),
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            if section_conflicts.exists():
                for sc in section_conflicts:
                    conflicts.append(f"Section {section.name} already has {sc.course.course_code} at this time")
            
            # Check faculty conflict
            if faculty:
                faculty_conflicts = Schedule.objects.filter(
                    faculty=faculty,
                    day=int(day),
                    start_time__lt=end_time,
                    end_time__gt=start_time
                )
                if faculty_conflicts.exists():
                    for fc in faculty_conflicts:
                        warnings.append(f"Faculty {faculty.full_name} is already teaching {fc.course.course_code} for {fc.section.name} at this time")
            
            # Check room conflict
            if room:
                room_conflicts = Schedule.objects.filter(
                    room=room,
                    day=int(day),
                    start_time__lt=end_time,
                    end_time__gt=start_time
                )
                if room_conflicts.exists():
                    for rc in room_conflicts:
                        warnings.append(f"Room {room.name} is already occupied by {rc.course.course_code} at this time")

            # If there are hard conflicts, return error
            if conflicts:
                return JsonResponse({
                    'success': False,
                    'errors': conflicts
                })

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

            response_data = {
                'success': True,
                'message': 'Schedule created successfully'
            }
            
            # Add warnings if any
            if warnings:
                response_data['warnings'] = warnings
                response_data['message'] = 'Schedule created with warnings'

            return JsonResponse(response_data)
            
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
        
        # Remember linked user (if any) so we can clean up that specific account
        linked_user = getattr(faculty, 'user', None)

        # Unassign faculty from any schedules (preserve schedule records)
        Schedule.objects.filter(faculty=faculty).update(faculty=None)

        # Delete the Faculty record
        faculty.delete()

        # If the Faculty had an associated Django User, delete that User only
        if linked_user:
            try:
                linked_user.delete()
            except Exception:
                # Don't fail the whole operation if user deletion has an issue
                pass

        log_activity(
            user=request.user,
            action='delete',
            entity_type='faculty',
            entity_name=faculty_name,
            message=f'Deleted faculty: {faculty_name} and cleaned up associated user account(s)'
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
                'id': schedule.id,
                'day': schedule.day,
                'start_time': schedule.start_time,
                'end_time': schedule.end_time,
                'duration': schedule.duration,
                'course_code': schedule.course.course_code,
                'course_title': schedule.course.descriptive_title,
                'course_color': schedule.course.color,
                'faculty': f"{schedule.faculty.first_name} {schedule.faculty.last_name}" if schedule.faculty else 'TBA',
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
    
    # Format schedule data for JavaScript
    schedule_data = []
    for schedule in schedules:
        schedule_data.append({
            'day': schedule.day,
            'start_time': schedule.start_time,
            'end_time': schedule.end_time,
            'duration': schedule.duration,
            'course_code': schedule.course.course_code,
            'course_title': schedule.course.descriptive_title,
            'course_color': schedule.course.color,
            'room': schedule.room.name if schedule.room else 'TBA',
            'section_name': schedule.section.name,
        })
    
    # Get specializations
    specializations = faculty.specialization.all()
    
    import json
    
    context = {
        'user': request.user,
        'faculty': faculty,
        'schedules': json.dumps(schedule_data),  # Serialize to JSON
        'time_slots': [],  # Will be generated by JavaScript
        'days': [],  # Will be generated by JavaScript
        'specializations': specializations,
    }
    
    return render(request, 'hello/staff_dashboard.html', context)

# ===== SECTION VIEWS =====

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def section_view(request):
    """Section management page"""
    # Get all sections with their related curriculum
    sections = Section.objects.select_related('curriculum').all().order_by('year_level', 'semester', 'name')
    
    # Calculate total units for each section
    for section in sections:
        unique_course_ids = section.schedules.values_list('course', flat=True).distinct()
        total = Course.objects.filter(id__in=unique_course_ids).aggregate(
            total=Sum('credit_units')
        )['total'] or 0
        section.calculated_total_units = total
    
    # Get all curricula for the add/edit section forms
    curricula = Curriculum.objects.all().order_by('-year')
    
    # Get all courses for schedule creation
    all_courses = Course.objects.all().order_by('course_code')
    
    # Get faculty and rooms for schedule modal
    faculty_list = Faculty.objects.all().order_by('last_name', 'first_name')
    room_list = Room.objects.all().order_by('campus', 'room_number')
    
    context = {
        'user': request.user,
        'sections': sections,
        'curricula': curricula,
        'all_courses': all_courses,
        'faculty_list': faculty_list,
        'room_list': room_list,
    }
    
    return render(request, 'hello/section.html', context)

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_section(request):
    """Add new section"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            year_level = int(request.POST.get('year_level'))
            semester = int(request.POST.get('semester'))
            curriculum_id = request.POST.get('curriculum')
            max_students = int(request.POST.get('max_students', 40))
            
            curriculum = Curriculum.objects.get(id=curriculum_id)
            
            # Check if section name already exists for this curriculum
            if Section.objects.filter(name=name, curriculum=curriculum).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['A section with this name already exists in the selected curriculum.']
                })
            
            section = Section(
                name=name,
                year_level=year_level,
                semester=semester,
                curriculum=curriculum,
                max_students=max_students,
                status='incomplete'
            )
            
            # This will validate the section name format
            section.full_clean()
            section.save()
            
            log_activity(
                user=request.user,
                action='add',
                entity_type='section',
                entity_name=section.name,
                message=f'Added section: {section.name} - Year {year_level}, Semester {semester}'
            )
            
            return JsonResponse({'success': True})
            
        except Curriculum.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Selected curriculum does not exist.']
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
            print(f"Error adding section: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [f'Error adding section: {str(e)}']
            })
    
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_section(request, section_id):
    """Edit existing section"""
    section = get_object_or_404(Section, id=section_id)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            year_level = int(request.POST.get('year_level'))
            semester = int(request.POST.get('semester'))
            curriculum_id = request.POST.get('curriculum')
            max_students = int(request.POST.get('max_students', 40))
            
            curriculum = Curriculum.objects.get(id=curriculum_id)
            
            # Check if section name already exists for this curriculum (excluding current section)
            if Section.objects.filter(name=name, curriculum=curriculum).exclude(id=section_id).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['A section with this name already exists in the selected curriculum.']
                })
            
            section.name = name
            section.year_level = year_level
            section.semester = semester
            section.curriculum = curriculum
            section.max_students = max_students
            
            section.full_clean()
            section.save()
            
            log_activity(
                user=request.user,
                action='edit',
                entity_type='section',
                entity_name=section.name,
                message=f'Edited section: {section.name} - Year {year_level}, Semester {semester}'
            )
            
            return JsonResponse({'success': True})
            
        except Curriculum.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Selected curriculum does not exist.']
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
            print(f"Error editing section: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
    
    # Return section data for editing
    return JsonResponse({
        'id': section.id,
        'name': section.name,
        'year_level': section.year_level,
        'semester': section.semester,
        'curriculum': section.curriculum.id,
        'max_students': section.max_students,
        'status': section.status
    })

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_section(request, section_id):
    """Delete section"""
    if request.method == 'POST':
        section = get_object_or_404(Section, id=section_id)
        section_name = section.name
        
        # Check if section has schedules
        if section.schedules.exists():
            return JsonResponse({
                'success': False,
                'errors': ['Cannot delete section with existing schedules. Delete schedules first.']
            })
        
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
        
        # Get all schedules for this section
        schedules = Schedule.objects.filter(section=section).select_related(
            'course', 'faculty', 'room'
        ).order_by('day', 'start_time')
        
        # Format schedule data
        schedule_data = []
        courses_map = {}
        
        for schedule in schedules:
            schedule_item = {
                'id': schedule.id,
                'day': schedule.day,
                'start_time': schedule.start_time,
                'end_time': schedule.end_time,
                'duration': schedule.duration,
                'course_code': schedule.course.course_code,
                'course_title': schedule.course.descriptive_title,
                'course_color': schedule.course.color,
                'faculty': f"{schedule.faculty.first_name} {schedule.faculty.last_name}" if schedule.faculty else 'TBA',
                'room': schedule.room.name if schedule.room else 'TBA',
                'section_name': schedule.section.name,
            }
            schedule_data.append(schedule_item)
            
            # Track unique courses for sidebar
            if schedule.course.id not in courses_map:
                courses_map[schedule.course.id] = {
                    'course_code': schedule.course.course_code,
                    'descriptive_title': schedule.course.descriptive_title,
                    'color': schedule.course.color,
                    'lecture_hours': schedule.course.lecture_hours,
                    'laboratory_hours': schedule.course.laboratory_hours,
                    'credit_units': schedule.course.credit_units
                }
        
        # Convert courses_map to list
        courses_list = list(courses_map.values())
        
        # Calculate total units
        total_units = sum(course['credit_units'] for course in courses_list)
        
        return JsonResponse({
            'success': True,
            'schedules': schedule_data,
            'courses': courses_list,
            'total_units': total_units,
            'section_info': {
                'name': section.name,
                'year_level': section.year_level,
                'semester': section.semester,
                'curriculum': str(section.curriculum),
                'max_students': section.max_students
            }
        })
    except Exception as e:
        import traceback
        print(f"Error in get_section_schedule: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
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

# ===== COURSE VIEWS =====

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def course_view(request):
    """Course management page"""
    # Get all curricula for the add/edit course forms
    curricula = Curriculum.objects.all().order_by('-year')

    # Read optional filters from querystring
    curriculum_id = request.GET.get('curriculum')
    selected_curriculum = None
    selected_year = request.GET.get('year')
    selected_semester = request.GET.get('semester')

    grouped_courses = {}
    academic_levels = []

    if curriculum_id:
        try:
            selected_curriculum = Curriculum.objects.get(id=curriculum_id)

            # Base queryset for this curriculum
            qs = Course.objects.filter(curriculum=selected_curriculum).order_by('year_level', 'semester', 'course_code')

            # Apply year/semester filters if present
            if selected_year:
                try:
                    qs = qs.filter(year_level=int(selected_year))
                except ValueError:
                    pass
            if selected_semester:
                try:
                    qs = qs.filter(semester=int(selected_semester))
                except ValueError:
                    pass

            # Build academic_levels (distinct year/semester pairs)
            levels = qs.values('year_level', 'semester').distinct().order_by('year_level', 'semester')
            for lvl in levels:
                yl = lvl['year_level']
                sem = lvl['semester']
                display = f"{('1st' if yl==1 else '2nd' if yl==2 else '3rd' if yl==3 else '4th')} Year, {('1st' if sem==1 else '2nd')} Semester"
                academic_levels.append({'year': yl, 'semester': sem, 'display': display})

            # Group courses by year_level and semester
            from collections import OrderedDict
            grouped = OrderedDict()
            for course in qs:
                key = f"{course.year_level}-{course.semester}"
                if key not in grouped:
                    display = f"{('1st' if course.year_level==1 else '2nd' if course.year_level==2 else '3rd' if course.year_level==3 else '4th')} Year, {('1st' if course.semester==1 else '2nd')} Semester"
                    grouped[key] = {
                        'display': display,
                        'courses': [],
                        'total_units': 0
                    }
                grouped[key]['courses'].append(course)
                grouped[key]['total_units'] += (course.credit_units or 0)

            grouped_courses = grouped

        except Curriculum.DoesNotExist:
            selected_curriculum = None

    # Provide the context expected by the template
    context = {
        'user': request.user,
        'curricula': curricula,
        'selected_curriculum': selected_curriculum,
        'selected_year': int(selected_year) if selected_year and selected_year.isdigit() else None,
        'selected_semester': int(selected_semester) if selected_semester and selected_semester.isdigit() else None,
        'grouped_courses': grouped_courses,
        'academic_levels': academic_levels,
    }

    return render(request, 'hello/course.html', context)

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_course(request):
    """Add new course"""
    if request.method == 'POST':
        try:
            curriculum_id = request.POST.get('curriculum')
            course_code = request.POST.get('course_code').strip().upper()
            descriptive_title = request.POST.get('descriptive_title').strip()
            laboratory_hours = int(request.POST.get('laboratory_hours', 0))
            lecture_hours = int(request.POST.get('lecture_hours', 0))
            credit_units = int(request.POST.get('credit_units', 0))
            year_level = int(request.POST.get('year_level'))
            semester = int(request.POST.get('semester'))
            
            curriculum = Curriculum.objects.get(id=curriculum_id)
            
            # Check if course code already exists in this curriculum
            if Course.objects.filter(course_code=course_code, curriculum=curriculum).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['A course with this code already exists in the selected curriculum.']
                })
            
            course = Course.objects.create(
                curriculum=curriculum,
                course_code=course_code,
                descriptive_title=descriptive_title,
                laboratory_hours=laboratory_hours,
                lecture_hours=lecture_hours,
                credit_units=credit_units,
                year_level=year_level,
                semester=semester
            )
            
            log_activity(
                user=request.user,
                action='add',
                entity_type='course',
                entity_name=f"{course.course_code} - {course.descriptive_title}",
                message=f'Added course: {course.course_code} - {course.descriptive_title}'
            )
            
            return JsonResponse({'success': True})
            
        except Curriculum.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Selected curriculum does not exist.']
            })
        except Exception as e:
            import traceback
            print(f"Error adding course: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [f'Error adding course: {str(e)}']
            })
    
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_course(request, course_id):
    """Edit existing course"""
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        try:
            curriculum_id = request.POST.get('curriculum')
            course_code = request.POST.get('course_code').strip().upper()
            descriptive_title = request.POST.get('descriptive_title').strip()
            laboratory_hours = int(request.POST.get('laboratory_hours', 0))
            lecture_hours = int(request.POST.get('lecture_hours', 0))
            credit_units = int(request.POST.get('credit_units', 0))
            year_level = int(request.POST.get('year_level'))
            semester = int(request.POST.get('semester'))
            
            curriculum = Curriculum.objects.get(id=curriculum_id)
            
            # Check if course code already exists in this curriculum (excluding current course)
            if Course.objects.filter(course_code=course_code, curriculum=curriculum).exclude(id=course_id).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['A course with this code already exists in the selected curriculum.']
                })
            
            course.curriculum = curriculum
            course.course_code = course_code
            course.descriptive_title = descriptive_title
            course.laboratory_hours = laboratory_hours
            course.lecture_hours = lecture_hours
            course.credit_units = credit_units
            course.year_level = year_level
            course.semester = semester
            
            course.save()
            
            log_activity(
                user=request.user,
                action='edit',
                entity_type='course',
                entity_name=f"{course.course_code} - {course.descriptive_title}",
                message=f'Edited course: {course.course_code} - {course.descriptive_title}'
            )
            
            return JsonResponse({'success': True})
            
        except Curriculum.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Selected curriculum does not exist.']
            })
        except Exception as e:
            import traceback
            print(f"Error editing course: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
    
    # Return course data for editing
    return JsonResponse({
        'id': course.id,
        'curriculum': course.curriculum.id,
        'course_code': course.course_code,
        'descriptive_title': course.descriptive_title,
        'laboratory_hours': course.laboratory_hours,
        'lecture_hours': course.lecture_hours,
        'credit_units': course.credit_units,
        'year_level': course.year_level,
        'semester': course.semester,
        'color': course.color
    })

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_course(request, course_id):
    """Delete course"""
    if request.method == 'POST':
        course = get_object_or_404(Course, id=course_id)
        course_name = f"{course.course_code} - {course.descriptive_title}"
        
        # Check if course has schedules
        if course.schedules.exists():
            return JsonResponse({
                'success': False,
                'errors': ['Cannot delete course with existing schedules. Delete schedules first.']
            })
        
        course.delete()
        
        log_activity(
            user=request.user,
            action='delete',
            entity_type='course',
            entity_name=course_name,
            message=f'Deleted course: {course_name}'
        )
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

# ===== CURRICULUM VIEWS =====

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def add_curriculum(request):
    """Add new curriculum"""
    if request.method == 'POST':
        try:
            name = request.POST.get('name').strip()
            year = int(request.POST.get('year'))
            
            # Check if curriculum already exists
            if Curriculum.objects.filter(name=name, year=year).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['A curriculum with this name and year already exists.']
                })
            
            curriculum = Curriculum.objects.create(
                name=name,
                year=year
            )
            
            log_activity(
                user=request.user,
                action='add',
                entity_type='curriculum',
                entity_name=f"{curriculum.name} ({curriculum.year})",
                message=f'Added curriculum: {curriculum.name} ({curriculum.year})'
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            import traceback
            print(f"Error adding curriculum: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [f'Error adding curriculum: {str(e)}']
            })
    
    return JsonResponse({'success': False})

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def edit_curriculum(request, curriculum_id):
    """Edit existing curriculum"""
    curriculum = get_object_or_404(Curriculum, id=curriculum_id)
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name').strip()
            year = int(request.POST.get('year'))
            
            # Check if curriculum with new name/year already exists (excluding current)
            if Curriculum.objects.filter(name=name, year=year).exclude(id=curriculum_id).exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['A curriculum with this name and year already exists.']
                })
            
            curriculum.name = name
            curriculum.year = year
            curriculum.save()
            
            log_activity(
                user=request.user,
                action='edit',
                entity_type='curriculum',
                entity_name=f"{curriculum.name} ({curriculum.year})",
                message=f'Edited curriculum: {curriculum.name} ({curriculum.year})'
            )
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            import traceback
            print(f"Error editing curriculum: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
    
    # Return curriculum data for editing
    return JsonResponse({
        'id': curriculum.id,
        'name': curriculum.name,
        'year': curriculum.year
    })

@login_required(login_url='admin_login')
@user_passes_test(is_admin, login_url='admin_login')
def delete_curriculum(request, curriculum_id):
    """Delete curriculum"""
    if request.method == 'POST':
        curriculum = get_object_or_404(Curriculum, id=curriculum_id)
        curriculum_name = f"{curriculum.name} ({curriculum.year})"
        
        # Check if curriculum has courses
        if curriculum.courses.exists():
            return JsonResponse({
                'success': False,
                'errors': ['Cannot delete curriculum with existing courses. Delete courses first.']
            })
        
        # Check if curriculum has sections
        if curriculum.sections.exists():
            return JsonResponse({
                'success': False,
                'errors': ['Cannot delete curriculum with existing sections. Delete sections first.']
            })
        
        curriculum.delete()
        
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
def generate_schedule(request):
    """Generate schedule automatically using AI/algorithm"""
    if request.method == 'POST':
        try:
            section_id = request.POST.get('section')
            section = Section.objects.get(id=section_id)
            
            # Get all courses for this section's year/semester/curriculum
            courses = Course.objects.filter(
                curriculum=section.curriculum,
                year_level=section.year_level,
                semester=section.semester
            )
            
            if not courses.exists():
                return JsonResponse({
                    'success': False,
                    'errors': ['No courses found for this section configuration.']
                })
            
            # Clear existing schedules for this section
            Schedule.objects.filter(section=section).delete()
            
            # Time slots: 7:30 AM to 9:30 PM
            time_slots = [
                ('07:30', '09:00'), ('09:00', '10:30'), ('10:30', '12:00'),
                ('13:00', '14:30'), ('14:30', '16:00'), ('16:00', '17:30'),
                ('17:30', '19:00'), ('19:00', '20:30')
            ]
            
            # Available days (0=Monday to 5=Saturday)
            days = [0, 1, 2, 3, 4, 5]
            
            # Get available faculty and rooms
            available_faculty = list(Faculty.objects.all())
            available_rooms = list(Room.objects.all())
            
            generated_schedules = []
            conflicts = []
            
            # Simple scheduling algorithm
            for course in courses:
                # Separate lecture and lab hours
                lecture_hours = course.lecture_hours
                lab_hours = course.laboratory_hours
                
                schedules_to_create = []
                
                # Handle lecture hours
                if lecture_hours > 0:
                    lecture_sessions = max(1, lecture_hours // 2)  # 1.5-2 hour sessions
                    schedules_to_create.append({
                        'type': 'lecture',
                        'sessions': lecture_sessions,
                        'duration_hours': lecture_hours / lecture_sessions
                    })
                
                # Handle lab hours
                if lab_hours > 0:
                    lab_sessions = max(1, lab_hours // 2)  # 1.5-2 hour sessions
                    schedules_to_create.append({
                        'type': 'laboratory',
                        'sessions': lab_sessions,
                        'duration_hours': lab_hours / lab_sessions
                    })
                
                # Schedule each type (lecture and/or lab)
                for schedule_type_info in schedules_to_create:
                    schedule_type = schedule_type_info['type']
                    sessions_needed = schedule_type_info['sessions']
                    
                    scheduled_sessions = 0
                    attempts = 0
                    max_attempts = 100
                    
                    while scheduled_sessions < sessions_needed and attempts < max_attempts:
                        attempts += 1
                        
                        # Random day and time slot
                        day = random.choice(days)
                        start_time, end_time = random.choice(time_slots)
                        
                        # Random faculty (prefer specialized)
                        faculty = None
                        specialized = [f for f in available_faculty if course in f.specialization.all()]
                        if specialized:
                            faculty = random.choice(specialized)
                        elif available_faculty:
                            faculty = random.choice(available_faculty)
                        
                        # Random room based on type
                        room = None
                        if available_rooms:
                            if schedule_type == 'laboratory':
                                lab_rooms = [r for r in available_rooms if r.room_type == 'laboratory']
                                room = random.choice(lab_rooms) if lab_rooms else random.choice(available_rooms)
                            else:
                                lecture_rooms = [r for r in available_rooms if r.room_type == 'lecture']
                                room = random.choice(lecture_rooms) if lecture_rooms else random.choice(available_rooms)
                        
                        # Check for conflicts
                        conflict = False
                        
                        # Check section conflict (same section, overlapping time)
                        section_conflicts = Schedule.objects.filter(
                            section=section,
                            day=day,
                            start_time__lt=end_time,
                            end_time__gt=start_time
                        )
                        if section_conflicts.exists():
                            conflict = True
                        
                        # Check faculty conflict
                        if faculty:
                            faculty_conflicts = Schedule.objects.filter(
                                faculty=faculty,
                                day=day,
                                start_time__lt=end_time,
                                end_time__gt=start_time
                            )
                            if faculty_conflicts.exists():
                                conflict = True
                        
                        # Check room conflict
                        if room:
                            room_conflicts = Schedule.objects.filter(
                                room=room,
                                day=day,
                                start_time__lt=end_time,
                                end_time__gt=start_time
                            )
                            if room_conflicts.exists():
                                conflict = True
                        
                        if not conflict:
                            # Create schedule
                            schedule = Schedule.objects.create(
                                course=course,
                                section=section,
                                faculty=faculty,
                                room=room,
                                day=day,
                                start_time=start_time,
                                end_time=end_time
                            )
                            generated_schedules.append(schedule)
                            scheduled_sessions += 1
                    
                    if scheduled_sessions < sessions_needed:
                        conflicts.append(f"{course.course_code} ({schedule_type}) - Only {scheduled_sessions}/{sessions_needed} sessions scheduled")
            
            # Update section status
            section.status = 'complete' if len(generated_schedules) > 0 else 'incomplete'
            section.save()
            
            # Log activity
            log_activity(
                user=request.user,
                action='add',
                entity_type='schedule',
                entity_name=f"Generated schedule for {section.name}",
                message=f'Auto-generated {len(generated_schedules)} schedule entries for {section.name}'
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully generated {len(generated_schedules)} schedule entries',
                'schedules_created': len(generated_schedules),
                'conflicts': conflicts,
                'section_id': section.id
            })
            
        except Section.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': ['Section not found']
            })
        except Exception as e:
            import traceback
            print(f"Error generating schedule: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'success': False,
                'errors': [f'Error generating schedule: {str(e)}']
            })
    
    return JsonResponse({
        'success': False,
        'errors': ['Invalid request method']
    })

@login_required
def edit_schedule(request, schedule_id):
    """Edit existing schedule entry"""
    schedule = get_object_or_404(Schedule, id=schedule_id)
    
    if request.method == 'POST':
        try:
            course_id = request.POST.get('course')
            faculty_id = request.POST.get('faculty')
            room_id = request.POST.get('room')
            day = request.POST.get('day')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            
            course = Course.objects.get(id=course_id)
            faculty = Faculty.objects.get(id=faculty_id) if faculty_id else None
            room = Room.objects.get(id=room_id) if room_id else None
            
            schedule.course = course
            schedule.faculty = faculty
            schedule.room = room
            schedule.day = int(day)
            schedule.start_time = start_time
            schedule.end_time = end_time
            
            schedule.full_clean()
            schedule.save()
            
            log_activity(
                user=request.user,
                action='edit',
                entity_type='schedule',
                entity_name=f"{course.course_code} - {schedule.section.name}",
                message=f'Edited schedule: {course.course_code} for {schedule.section.name}'
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Schedule updated successfully'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': [str(e)]
            })
    
    # Return schedule data for editing
    return JsonResponse({
        'id': schedule.id,
        'course': schedule.course.id,
        'faculty': schedule.faculty.id if schedule.faculty else '',
        'room': schedule.room.id if schedule.room else '',
        'day': schedule.day,
        'start_time': schedule.start_time,
        'end_time': schedule.end_time
    })

