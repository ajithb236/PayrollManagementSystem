from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('assign_employee/', views.assign_employee, name='assign_employee'),
    path('update_payscales/', views.update_payscales, name='update_payscales'),
    path('generate_reports/', views.generate_reports, name='generate_reports'),
    path('profile/', views.hr_profile, name='hr_profile'),
    path('manage_employees/', views.manage_employees1, name='manage_employees'),
    path('metrics_dashboard/', views.hr_metrics_dashboard, name='hr_metrics_dashboard'),
    path('attendance_details/', views.attendance_details, name='attendance_details'),
    path('approve_leave/', views.approve_leave_requests, name='approve_leave_requests'),
    # Other HR URLs
]