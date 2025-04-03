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
        messages.error(request,"Not an Employee")
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
                VALUES (%s, %s, 8, 0, 'Present')
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
def view_salary(request):
    # Fetch employee salary details
    user_id = request.user.id
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT e.employee_id, e.name, p.allowances, j.salary_range
            FROM payroll_employee e
            LEFT JOIN payroll_payroll p ON e.employee_id = p.employee_id
            LEFT JOIN payroll_jobsalaryrange j ON e.job_id = j.job_id
            WHERE e.user_id = %s
            """, [user_id]
        )
        salary_details = cursor.fetchone()

    if not salary_details:
        messages.error(request, "Salary details not found.")
        return redirect('employee_dashboard')

    # Prepare salary data for the template
    salary_data = {
        'employee_id': salary_details[0],
        'name': salary_details[1],
        'allowances': salary_details[2],
        'salary_range': salary_details[3]
    }
    return render(request, 'employee/salary.html', {'salary': salary_data})


@login_required
def profile(request):
    user_id = request.user.id

    # Fetch employee details
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT e.name, e.contact, e.email, e.address, e.gender, e.date_of_birth,e.date_joined
            FROM payroll_employee e
            WHERE e.user_id = %s
            """, [user_id]
        )
        employee = cursor.fetchone()

    if not employee:
        messages.error(request, "Employee record not found.")
        return redirect('employee_dashboard')

    # Handle POST request for updating profile
    if request.method == 'POST':
        address = request.POST.get('address')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('date_of_birth')

        # Update only the editable fields
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE payroll_employee
                SET address = %s, gender = %s, date_of_birth = %s
                WHERE user_id = %s
                """, [address, gender, date_of_birth, user_id]
            )
        messages.success(request, "Your profile has been updated successfully.")
        return redirect('profile')  # Redirect back to the profile page

    # Prepare employee data for the template
    employee_data = {
        'name': employee[0],
        'contact': employee[1],
        'email': employee[2],
        'address': employee[3],
        'gender': employee[4],
        'date_of_birth': employee[5],
        'date_joined':employee[6]
    }

    return render(request, 'employee/profile.html', {'employee': employee_data})
@login_required
def attendance_tracker(request):
    user_id = request.user.id

    # Fetch employee attendance details
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT a.date, a.hours_worked, a.overtime_hours, a.leave_status
            FROM payroll_attendance a
            INNER JOIN payroll_employee e ON a.employee_id = e.employee_id
            WHERE e.user_id = %s
            ORDER BY a.date DESC
            """, [user_id]
        )
        attendance_records = cursor.fetchall()

    # Prepare attendance data for the template
    attendance_data = [
        {
            'date': record[0],
            'hours_worked': record[1],
            'overtime_hours': record[2],
            'leave_status': record[3]
        }
        for record in attendance_records
    ]
    return render(request, 'employee/attendance_details.html', {'attendance': attendance_data})

@login_required
def clock_overtime(request):
    user_id = request.user.id

    # Fetch employee ID
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT employee_id FROM payroll_employee
            WHERE user_id = %s
            """, [user_id]
        )
        employee = cursor.fetchone()

    if not employee:
        messages.error(request, "Employee record not found.")
        return redirect('employee_dashboard')

    employee_id = employee[0]
    today = datetime.now().date()

    if request.method == 'POST':
        overtime_hours = request.POST.get('overtime_hours')

        if not overtime_hours or not overtime_hours.isdigit() or int(overtime_hours) < 0:
            messages.error(request, "Please enter a valid number of overtime hours.")
            return redirect('clock_overtime')

        # Update overtime hours for today's attendance
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE payroll_attendance
                SET overtime_hours = %s
                WHERE employee_id = %s AND date = %s
                """, [overtime_hours, employee_id, today]
            )
        messages.success(request, f"Overtime hours updated to {overtime_hours} for today.")
        return redirect('employee_dashboard')
    return render(request, 'employee/clock_overtime.html')

def error_page(request):
    return render(request, 'employee/error.html')  # Ensure you have an error.html template
def logout(request):
    from django.contrib.auth import logout
    messages.success(request, "Logged out successfully.")
    logout(request)
    return redirect("login")