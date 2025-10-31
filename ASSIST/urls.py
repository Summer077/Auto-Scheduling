from django.contrib import admin
from django.urls import path, include
from hello import views

urlpatterns = [
    # Custom admin login - MUST be first!
    path('admin/login/', views.admin_login, name='admin_login'),
    
    # Django default admin (different URL)
    path('django-admin/', admin.site.urls),
    
    # Include hello app URLs
    path('', include('hello.urls')),
]