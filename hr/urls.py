from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('assign_employee/', views.assign_employee, name='assign_employee'),
    path('update_payscales/', views.update_payscales, name='update_payscales'),
    path('generate_reports/', views.generate_reports, name='generate_reports'),
    path('profile/', views.hr_profile, name='hr_profile'),
    path('manage_employees/', views.manage_employees, name='manage_employees'),
    # Other HR URLs
]