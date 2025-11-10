from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Dashboards
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    
    # Sections
    path('admin/section/', views.section_view, name='section_view'),  
    path('admin/section/add/', views.add_section, name='add_section'),
    path('admin/section/edit/<int:section_id>/', views.edit_section, name='edit_section'),
    path('admin/section/delete/<int:section_id>/', views.delete_section, name='delete_section'),
    path('admin/section/<int:section_id>/schedule-data/', views.get_section_schedule, name='get_section_schedule'),
    path('admin/section/<int:section_id>/toggle-status/', views.toggle_section_status, name='toggle_section_status'),
    
    # Courses
    path('admin/course/', views.course_view, name='course_view'),
    path('admin/course/add/', views.add_course, name='add_course'),
    path('admin/course/edit/<int:course_id>/', views.edit_course, name='edit_course'),
    path('admin/course/delete/<int:course_id>/', views.delete_course, name='delete_course'),
    
    # Schedules
    path('admin/schedule/', views.schedule_view, name='schedule_view'),
    path('admin/schedule/add/', views.add_schedule, name='add_schedule'),
    path('admin/schedule/delete/<int:schedule_id>/', views.delete_schedule, name='delete_schedule'),

    # Curriculum operations
    path('admin/curriculum/add/', views.add_curriculum, name='add_curriculum'),
    path('admin/curriculum/delete/<int:curriculum_id>/', views.delete_curriculum, name='delete_curriculum'),
    path('curriculum/edit/<int:curriculum_id>/', views.edit_curriculum, name='edit_curriculum'),
    
    # Faculty CRUD operations
    path('admin/faculty/', views.faculty_view, name='faculty_view'),
    path('admin/faculty/add/', views.add_faculty, name='add_faculty'),
    path('admin/faculty/edit/<int:faculty_id>/', views.edit_faculty, name='edit_faculty'),
    path('admin/faculty/delete/<int:faculty_id>/', views.delete_faculty, name='delete_faculty'),
    path('admin/faculty/<int:faculty_id>/schedule-data/', views.get_faculty_schedule, name='get_faculty_schedule'),

    # Room CRUD operations 
    path('admin/room/', views.room_view, name='room_view'),
    path('admin/room/add/', views.add_room, name='add_room'),
    path('admin/room/edit/<int:room_id>/', views.edit_room, name='edit_room'),
    path('admin/room/delete/<int:room_id>/', views.delete_room, name='delete_room'),
    path('admin/room/<int:room_id>/schedule-data/', views.get_room_schedule, name='get_room_schedule'),

    # Auth
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    path('admin/password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='hello/password_reset.html'
         ), 
         name='password_reset'),
]