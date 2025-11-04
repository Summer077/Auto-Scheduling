from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/section/', views.section_view, name='section_view'),  
    path('admin/course/', views.course_view, name='course_view'),
    path('admin/course/add/', views.add_course, name='add_course'),
    path('admin/course/edit/<int:course_id>/', views.edit_course, name='edit_course'),
    path('admin/course/delete/<int:course_id>/', views.delete_course, name='delete_course'),
    path('admin/section/<int:section_id>/schedule-data/', views.get_section_schedule, name='get_section_schedule'),
    
    # Add section CRUD operations
    path('admin/section/add/', views.add_section, name='add_section'),
    path('admin/section/edit/<int:section_id>/', views.edit_section, name='edit_section'),
    path('admin/section/delete/<int:section_id>/', views.delete_section, name='delete_section'),
    
    # Add section CRUD operations
    path('admin/section/add/', views.add_section, name='add_section'),
    path('admin/section/edit/<int:section_id>/', views.edit_section, name='edit_section'),
    path('admin/section/delete/<int:section_id>/', views.delete_section, name='delete_section'),

    path('admin/curriculum/add/', views.add_curriculum, name='add_curriculum'),
    path('admin/curriculum/delete/<int:curriculum_id>/', views.delete_curriculum, name='delete_curriculum'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    path('curriculum/edit/<int:curriculum_id>/', views.edit_curriculum, name='edit_curriculum'),
    
    path('admin/password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='hello/password_reset.html'
         ), 
         name='password_reset'),
]