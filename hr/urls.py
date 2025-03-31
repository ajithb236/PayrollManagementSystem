from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('manage_employee/', views.manage_employee, name='manage_employee'),
    path('update_payscales/', views.update_payscales, name='update_payscales'),
    path('generate_reports/', views.generate_reports, name='generate_reports'),
    # Other HR URLs
]