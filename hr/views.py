from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from payroll.models import Job  # Import Job from Payroll app
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.contrib import messages
@login_required
def hr_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'HR':
        return redirect('login')  # Ensure only HR users can access this page
    return render(request, 'hr/dashboard.html')


@login_required
def update_payscales(request):
    if request.method == 'POST':
        job_id = request.POST.get('job_id')
        salary_range = request.POST.get('salary_range')
        job = get_object_or_404(Job, pk=job_id)
        job.salary_range = salary_range
        job.save()
        return redirect('update_payscales')
    jobs = Job.objects.all()
    return render(request, 'hr/update_payscales.html', {'jobs': jobs})

@login_required
def generate_reports(request):
    # Logic to generate reports
    return render(request, 'hr/generate_reports.html')

@login_required
def manage_employee(request):
    return render(request, 'hr/manage_employee.html')

@login_required
def assign_employee(request):
    # Ensure only HR users can access this page
    if not request.user.is_authenticated or request.user.role != 'HR':
        return redirect('login')

    # Fetch employees with NULL department and job using raw SQL
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT e.employee_id, e.name, e.contact, e.email
            FROM payroll_employee e
            WHERE e.department_id IS NULL AND e.job_id IS NULL
        """)
        employees = cursor.fetchall()

    # Fetch all departments and jobs for the dropdown options
    with connection.cursor() as cursor:
        cursor.execute("SELECT department_id, department_name FROM payroll_department")
        departments = cursor.fetchall()

        cursor.execute("SELECT job_id, job_title FROM payroll_job")
        jobs = cursor.fetchall()

    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        department_id = request.POST.get('department_id')
        job_id = request.POST.get('job_id')

        # Update the employee's department and job using raw SQL
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE payroll_employee
                SET department_id = %s, job_id = %s
                WHERE employee_id = %s
            """, [department_id, job_id, employee_id])
        messages.success(request, 'Employee assigned successfully!')
        return redirect('assign_employee')

    return render(request, 'hr/assign_employee.html', {
        'employees': employees,
        'departments': departments,
        'jobs': jobs
    })