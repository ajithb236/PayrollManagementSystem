from django.urls import path
from .views import employee_dashboard
from .views import error_page
from .views import logout
from .views import profile
urlpatterns = [
    path("dashboard/", employee_dashboard, name="employee_dashboard"),
    path('error/', error_page, name='error_page'),  # Make sure this exists
    path('logout/',logout,name='logout'),# Logout URL
    path('profile/', profile, name='profile'),  # Profile URL
]
