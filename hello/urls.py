from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/course/', views.course_view, name='course_view'),
    path('admin/course/add/', views.add_course, name='add_course'),
    path('admin/course/edit/<int:course_id>/', views.edit_course, name='edit_course'),
    path('admin/course/delete/<int:course_id>/', views.delete_course, name='delete_course'),
    path('admin/curriculum/add/', views.add_curriculum, name='add_curriculum'),
    path('admin/curriculum/delete/<int:curriculum_id>/', views.delete_curriculum, name='delete_curriculum'),
    path('admin/logout/', views.admin_logout, name='admin_logout'),
    path('curriculum/edit/<int:curriculum_id>/', views.edit_curriculum, name='edit_curriculum'),
    
    # Password reset URLs (optional)
    path('admin/password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='hello/password_reset.html'
         ), 
         name='password_reset'),
]