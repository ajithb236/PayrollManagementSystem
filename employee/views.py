# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from payroll.models import Employee  # Import Employee from Payroll app
from django.db import connection
from django.contrib import messages

from payroll.models import Employee, Attendance
from datetime import datetime

@login_required
def employee_dashboard(request):
    user_id = request.user.id

    # Check if the user is an employee
    if request.user.role != "Employee":
        return redirect("login")  # Unauthorized access redirects to login

    # Fetch employee details
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT e.employee_id, e.name, e.email, e.contact, e.address, e.gender, e.date_of_birth, j.job_title, d.department_name
            FROM payroll_employee e
            LEFT JOIN payroll_job j ON e.job_id = j.job_id
            LEFT JOIN payroll_department d ON e.department_id = d.department_id
            WHERE e.user_id = %s
            """, [user_id]
        )
        employee = cursor.fetchone()

    # Check if any required fields are missing
    if not employee or not employee[2] or not employee[4] or not employee[5] or not employee[6]:
        # Add a message to inform the user
        messages.error(request, "You must update your profile details to access the dashboard.")
        return redirect('profile')  # Redirect to the profile page

    # Automatically mark attendance
    today = datetime.now().date()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT attendance_id FROM payroll_attendance
            WHERE employee_id = %s AND date = %s
            """, [employee[0], today]
        )
        attendance = cursor.fetchone()

        if not attendance:
            cursor.execute(
                """
                INSERT INTO payroll_attendance (employee_id, date, hours_worked, overtime_hours, leave_status)
                VALUES (%s, %s, 0, 0, 'Present')
                """, [employee[0], today]
            )

    # Prepare employee data for the dashboard
    employee_data = {
        'employee_id': employee[0],
        'name': employee[1],
        'email': employee[2],
        'contact_number': employee[3],
        'address': employee[4],
        'gender': employee[5],
        'date_of_birth': employee[6],
        'job_title': employee[7],
        'department_name': employee[8],
        'current_date': datetime.now().strftime('%A, %d %B %Y'),
        'current_time': datetime.now().strftime('%I:%M %p')
    }
    return render(request, 'employee/dashboard.html', {'setup_needed': False, 'employee': employee_data})

@login_required
def profile(request):
    user_id = request.user.id

    # Fetch employee details
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT e.name, e.contact, e.email, e.address, e.gender, e.date_of_birth
            FROM payroll_employee e
            WHERE e.user_id = %s
            """, [user_id]
        )
        employee = cursor.fetchone()

    if request.method == 'POST':
        # name = request.POST.get('name')
        # contact = request.POST.get('contact')
        # email = request.POST.get('email')
        address = request.POST.get('address')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('date_of_birth')

        # Update employee details
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE payroll_employee
                SET address = %s, gender = %s, date_of_birth = %s
                WHERE user_id = %s
                """, [address, gender, date_of_birth, user_id]
            )
        messages.success(request, "Your profile has been updated successfully.")
        return redirect('employee_dashboard')
    employee_data = {
        'address': employee[0],
        'gender': employee[1],
        'date_of_birth': employee[2]
    }

    return render(request, 'employee/profile.html', {'employee': employee_data})
def error_page(request):
    return render(request, 'employee/error.html')  # Ensure you have an error.html template
def logout(request):
    from django.contrib.auth import logout
    messages.success(request, "Logged out successfully.")
    logout(request)
    return redirect("login")