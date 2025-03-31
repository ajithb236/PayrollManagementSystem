# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from payroll.models import Employee  # Import Employee from Payroll app
from django.db import connection

@login_required
def employee_dashboard(request):
    user_id = request.user.id  
    if request.user.role != "Employee":
        return redirect("login")  # Unauthorized access redirects to login
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT e.employee_id, e.name, e.email, e.contact, j.job_title, d.department_name
            FROM payroll_employee e
            LEFT JOIN payroll_job j ON e.job_id = j.job_id
            LEFT JOIN payroll_department d ON e.department_id = d.department_id
            WHERE e.user_id = %s
            """, [user_id]
        )
        employee = cursor.fetchone()

    if not employee or employee[4] is None or employee[5] is None:
        return render(request, 'employee/dashboard.html', {'setup_needed': True})

    employee_data = {
        'employee_id': employee[0],
        'Name': employee[1],
        'email': employee[2],
        'contact_number': employee[3],
        'job_title': employee[4],
        'department_name': employee[5]
    }

    return render(request, 'employee/dashboard.html', {'setup_needed': False, 'employee': employee_data})


def error_page(request):
    return render(request, 'employee/error.html')  # Ensure you have an error.html template
def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect("login")