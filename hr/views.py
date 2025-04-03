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
        messages.error(request,"Not an HR")
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
def hr_profile(request):
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
        return redirect('hr_dashboard')

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
        return redirect('hr_profile')  # Redirect back to the profile page

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

    return render(request, 'hr/profile.html', {'employee': employee_data})
@login_required
def generate_reports(request):
    # Logic to generate reports
    return render(request, 'hr/generate_reports.html')

@login_required
def manage_employee1(request):
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

@login_required
def manage_employees(request):
    # Ensure only HR users can access this page
    if not request.user.is_authenticated or request.user.role != 'HR':
        messages.error(request, "Access denied. Only HR users can access this page.")
        return redirect('login')

    # Fetch all departments except the HR department for the dropdown
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT department_id, department_name
            FROM payroll_department
            WHERE department_name != 'HR'
            """
        )
        departments = cursor.fetchall()

    employees = []
    selected_department = None

    # If a department is selected, fetch employees in that department
    if request.method == 'POST' and 'department_id' in request.POST:
        selected_department = request.POST.get('department_id')
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT e.employee_id, e.name, e.contact, e.email, j.job_title, d.department_name,
                       COALESCE(b.bonus_amount, 0) AS bonus
                FROM payroll_employee e
                LEFT JOIN payroll_job j ON e.job_id = j.job_id
                LEFT JOIN payroll_department d ON e.department_id = d.department_id
                LEFT JOIN payroll_payroll p ON e.employee_id = p.employee_id
                LEFT JOIN payroll_bonus b ON b.payroll_id = p.payroll_id
                WHERE e.department_id = %s
                """, [selected_department]
            )
            employees = cursor.fetchall()

    # Handle reassignment or bonus update
    if request.method == 'POST' and 'employee_id' in request.POST:
        employee_id = request.POST.get('employee_id')
        new_department_id = request.POST.get('new_department_id')
        new_job_id = request.POST.get('new_job_id')
        bonus = request.POST.get('bonus')

        # Update employee's department, job, and bonus
        with connection.cursor() as cursor:
            if new_department_id:
                cursor.execute(
                    "UPDATE payroll_employee SET department_id = %s WHERE employee_id = %s",
                    [new_department_id, employee_id]
                )
            if new_job_id:
                cursor.execute(
                    "UPDATE payroll_employee SET job_id = %s WHERE employee_id = %s",
                    [new_job_id, employee_id]
                )
            if bonus:
                # Fetch the payroll ID for the employee
                cursor.execute(
                    "SELECT payroll_id FROM payroll_payroll WHERE employee_id = %s",
                    [employee_id]
                )
                payroll = cursor.fetchone()
                if payroll:
                    payroll_id = payroll[0]
                    cursor.execute(
                        """
                        INSERT INTO payroll_bonus (payroll_id, bonus_amount)
                        VALUES (%s, %s)
                        ON DUPLICATE KEY UPDATE bonus_amount = %s
                        """, [payroll_id, bonus, bonus]
                    )
        messages.success(request, "Employee details updated successfully!")
        return redirect('manage_employees')

    # Fetch all jobs for the dropdown
    with connection.cursor() as cursor:
        cursor.execute("SELECT job_id, job_title FROM payroll_job")
        jobs = cursor.fetchall()

    return render(request, 'hr/manage_employee.html', {
        'departments': departments,
        'employees': employees,
        'jobs': jobs,
        'selected_department': selected_department
    })