from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.employee_dashboard, name="employee_dashboard"),
    path('error/', views.error_page, name='error_page'),  # Make sure this exists
    path('logout/',views.logout,name='logout'),# Logout URL
    path('profile/', views.profile, name='profile'),  # Profile URL
    path('salary/', views.view_salary, name='salary'),  # Salary URL
    path('attendance/', views.attendance_tracker, name='attendance'),  # Attendance URL
    path("clock_overtime/", views.clock_overtime, name="clock_overtime"),  # Clock Overtime URL
    path("transactions/",views.transaction_history,name="transaction_history"),
    path("request_leave/",views.request_leave,name="request_leave"),
    path("leave_balance/",views.leave_balance,name="leave_balance"),
]
