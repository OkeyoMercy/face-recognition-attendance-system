from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'), # Set login as the default page
    path('logout/', views.logout_view, name='logout'),
    path('admin-redirect/', views.admin_login_redirect, name='admin_redirect'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('register/', views.register_student, name='register_student'),
    path('tracking/', views.tracking, name='tracking'),
    path('scanner/', views.scanner, name='scanner'),
    path('process_scan/', views.process_scan, name='process_scan'),
    path('export_csv/', views.export_csv, name='export_csv'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
]
