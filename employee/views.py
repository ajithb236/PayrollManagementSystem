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
    
    if not employee[7] or not employee[8]:
        # Add a message to inform the user
        messages.error(request, "Contact HR to assign a job and department.")
        return render(request, 'employee/dashboard.html', {'setup_needed': True})  # Show setup needed message
    if not employee or not employee[2] or not employee[4] or not employee[5] or not employee[6]:
        # Add a message to inform the user
        messages.error(request, "You must update your profile details to access the dashboard.")
        return redirect('profile')  # Redirect to the profile page
    else:
        pass
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
@login_required
def view_salary(request):
    user_id = request.user.id
    
    # Get current month and year for filtering
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    with connection.cursor() as cursor:
        # Fetch employee basic details and base salary
        cursor.execute(
            """
            SELECT e.employee_id, e.name, j.job_title, jsr.salary_range, p.payroll_id, p.allowances
            FROM payroll_employee e
            LEFT JOIN payroll_job j ON e.job_id = j.job_id
            LEFT JOIN payroll_jobsalaryrange jsr ON j.job_id = jsr.job_id
            LEFT JOIN payroll_payroll p ON e.employee_id = p.employee_id
            WHERE e.user_id = %s
            """, [user_id]
        )
        employee_basic = cursor.fetchone()
        
        if not employee_basic:
            messages.error(request, "Salary details not found. Please contact HR.")
            return redirect('employee_dashboard')
        
        employee_id = employee_basic[0]
        payroll_id = employee_basic[4]
        base_salary = float(employee_basic[3]) if employee_basic[3] else 0
        
        # Fetch deductions
        cursor.execute(
            """
            SELECT tax_amount, other_deductions
            FROM payroll_deduction
            WHERE payroll_id = %s
            """, [payroll_id]
        )
        deductions = cursor.fetchone()
        tax_amount = float(deductions[0]) if deductions and deductions[0] else 0
        other_deductions = float(deductions[1]) if deductions and deductions[1] else 0
        
        # Fetch bonus
        cursor.execute(
            """
            SELECT bonus_amount
            FROM payroll_bonus
            WHERE payroll_id = %s
            """, [payroll_id]
        )
        bonus_record = cursor.fetchone()
        bonus_amount = float(bonus_record[0]) if bonus_record else 0
        
        # Calculate overtime pay (for current month)
        cursor.execute(
            """
            SELECT SUM(overtime_hours)
            FROM payroll_attendance
            WHERE employee_id = %s
            AND MONTH(date) = %s AND YEAR(date) = %s
            """, [employee_id, current_month, current_year]
        )
        overtime_result = cursor.fetchone()
        overtime_hours = float(overtime_result[0]) if overtime_result and overtime_result[0] else 0
        
        # Calculate hourly rate (assuming 160 working hours per month)
        hourly_rate = base_salary / 160
        overtime_pay = overtime_hours * hourly_rate * 2  # Double rate for overtime
        
        # Calculate allowances breakdown (typical Indian structure)
        total_allowances = float(employee_basic[5]) if employee_basic[5] else 0
        
        # Calculate standard components
        hra = base_salary * 0.40  # 40% of base salary
        da = base_salary * 0.10    # 10% of base salary
        ta = 3200  # Standard transport allowance
        special_allowance = total_allowances - (hra + da + ta)
        special_allowance = max(0, special_allowance)  # Ensure it's not negative
        
        # Calculate EPF (12% of basic salary)
        epf = base_salary * 0.12
        
        # Professional Tax
        prof_tax = 200
        
        # Calculate gross and net salary
        gross_salary = base_salary + total_allowances + bonus_amount + overtime_pay
        total_deductions = tax_amount + other_deductions + epf + prof_tax
        net_salary = gross_salary - total_deductions
        
        # Year to date calculations
        cursor.execute(
            """
            SELECT SUM(overtime_hours)
            FROM payroll_attendance
            WHERE employee_id = %s
            AND YEAR(date) = %s
            """, [employee_id, current_year]
        )
        ytd_overtime_result = cursor.fetchone()
        ytd_overtime = float(ytd_overtime_result[0]) if ytd_overtime_result and ytd_overtime_result[0] else 0
        ytd_overtime_pay = ytd_overtime * hourly_rate * 2
        
        ytd_gross = (base_salary + total_allowances) * current_month + bonus_amount + ytd_overtime_pay
        ytd_deductions = total_deductions * current_month
        ytd_net = ytd_gross - ytd_deductions

    salary_data = {
        'employee_name': employee_basic[1],
        'job_title': employee_basic[2],
        'month': datetime.now().strftime('%B %Y'),
        'base_salary': round(base_salary, 2),
        'allowances': {
            'hra': round(hra, 2),
            'da': round(da, 2),
            'ta': round(ta, 2),
            'special': round(special_allowance, 2),
            'total': round(total_allowances, 2)
        },
        'overtime': {
            'hours': overtime_hours,
            'rate': round(hourly_rate * 2, 2),
            'pay': round(overtime_pay, 2)
        },
        'bonus': round(bonus_amount, 2),
        'deductions': {
            'epf': round(epf, 2),
            'tax': round(tax_amount, 2),
            'prof_tax': prof_tax,
            'other': round(other_deductions, 2),
            'total': round(total_deductions + prof_tax, 2)  # Include prof_tax in total
        },
        'gross_salary': round(gross_salary, 2),
        'net_salary': round(net_salary, 2),
        'ytd': {
            'gross': round(ytd_gross, 2),
            'deductions': round(ytd_deductions, 2),
            'net': round(ytd_net, 2)
        }
    }
    
    return render(request, 'employee/salary.html', {'salary': salary_data})
@login_required
def view_salary1(request):
    user_id = request.user.id
    
    # Get current month and year for filtering
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    with connection.cursor() as cursor:
        # Fetch employee basic details and base salary
        cursor.execute(
            """
            SELECT e.employee_id, e.name, j.job_title, jsr.salary_range, p.payroll_id, p.allowances
            FROM payroll_employee e
            LEFT JOIN payroll_job j ON e.job_id = j.job_id
            LEFT JOIN payroll_jobsalaryrange jsr ON j.job_id = jsr.job_id
            LEFT JOIN payroll_payroll p ON e.employee_id = p.employee_id
            WHERE e.user_id = %s
            """, [user_id]
        )
        employee_basic = cursor.fetchone()
        
        if not employee_basic:
            messages.error(request, "Salary details not found. Please contact HR.")
            return redirect('employee_dashboard')
        
        employee_id = employee_basic[0]
        payroll_id = employee_basic[4]
        base_salary = float(employee_basic[3]) if employee_basic[3] else 0
        
        # Fetch deductions
        cursor.execute(
            """
            SELECT tax_amount, other_deductions
            FROM payroll_deduction
            WHERE payroll_id = %s
            """, [payroll_id]
        )
        deductions = cursor.fetchone()
        tax_amount = float(deductions[0]) if deductions and deductions[0] else 0
        other_deductions = float(deductions[1]) if deductions and deductions[1] else 0
        
        # Fetch bonus
        cursor.execute(
            """
            SELECT bonus_amount
            FROM payroll_bonus
            WHERE payroll_id = %s
            """, [payroll_id]
        )
        bonus_record = cursor.fetchone()
        bonus_amount = float(bonus_record[0]) if bonus_record else 0
        
        # Calculate overtime pay (for current month)
        cursor.execute(
            """
            SELECT SUM(overtime_hours)
            FROM payroll_attendance
            WHERE employee_id = %s
            AND MONTH(date) = %s AND YEAR(date) = %s
            """, [employee_id, current_month, current_year]
        )
        overtime_hours = cursor.fetchone()[0] or 0
        
        # Calculate hourly rate (assuming 160 working hours per month)
        hourly_rate = base_salary / 160
        overtime_pay = float(overtime_hours) * hourly_rate * 2  # Double rate for overtime
        
        # Calculate allowances breakdown (typical Indian structure)
        total_allowances = float(employee_basic[5]) if employee_basic[5] else 0
        
        # Calculate standard components
        hra = base_salary * 0.40  # 40% of base salary
        da = base_salary * 0.10    # 10% of base salary
        ta = 3200  # Standard transport allowance
        special_allowance = total_allowances - (hra + da + ta)
        special_allowance = max(0, special_allowance)  # Ensure it's not negative
        
        # Calculate EPF (12% of basic salary)
        epf = base_salary * 0.12
        
        # Calculate gross and net salary
        gross_salary = base_salary + total_allowances + bonus_amount + overtime_pay
        total_deductions = tax_amount + other_deductions + epf
        net_salary = gross_salary - total_deductions
        
        # Year to date calculations
        cursor.execute(
            """
            SELECT SUM(overtime_hours)
            FROM payroll_attendance
            WHERE employee_id = %s
            AND YEAR(date) = %s
            """, [employee_id, current_year]
        )
        ytd_overtime = cursor.fetchone()[0] or 0
        ytd_overtime_pay = float(ytd_overtime) * hourly_rate * 2
        
        ytd_gross = (base_salary + total_allowances) * current_month + bonus_amount + ytd_overtime_pay
        ytd_deductions = total_deductions * current_month
        ytd_net = ytd_gross - ytd_deductions

    salary_data = {
        'employee_name': employee_basic[1],
        'job_title': employee_basic[2],
        'month': datetime.now().strftime('%B %Y'),
        'base_salary': round(base_salary, 2),
        'allowances': {
            'hra': round(hra, 2),
            'da': round(da, 2),
            'ta': round(ta, 2),
            'special': round(special_allowance, 2),
            'total': round(total_allowances, 2)
        },
        'overtime': {
            'hours': overtime_hours,
            'rate': round(hourly_rate * 2, 2),
            'pay': round(overtime_pay, 2)
        },
        'bonus': round(bonus_amount, 2),
        'deductions': {
            'epf': round(epf, 2),
            'tax': round(tax_amount, 2),
            'other': round(other_deductions, 2),
            'total': round(total_deductions, 2)
        },
        'gross_salary': round(gross_salary, 2),
        'net_salary': round(net_salary, 2),
        'ytd': {
            'gross': round(ytd_gross, 2),
            'deductions': round(ytd_deductions, 2),
            'net': round(ytd_net, 2)
        }
    }
    
    return render(request, 'employee/salary.html', {'salary': salary_data})
def error_page(request):
    return render(request, 'employee/error.html')  # Ensure you have an error.html template
def logout(request):
    from django.contrib.auth import logout
    messages.success(request, "Logged out successfully.")
    logout(request)
    return redirect("login")