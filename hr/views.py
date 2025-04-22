from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from payroll.models import Job  
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime, timedelta
import calendar

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
def hr_metrics_dashboard(request):
    # Ensure only HR users can access this page
    if not request.user.is_authenticated or request.user.role != 'HR':
        messages.error(request, "Access denied. Only HR users can access this page.")
        return redirect('login')
    
    metrics = {}
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(employee_id) FROM payroll_employee
        """)
        total = cursor.fetchone()
        metrics['total_employees'] = total[0] if total and total[0] else 0
    
    # 1. Department headcount metrics
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT d.department_name, COUNT(e.employee_id) as headcount
            FROM payroll_department d
            LEFT JOIN payroll_employee e ON d.department_id = e.department_id
            GROUP BY d.department_id, d.department_name
            ORDER BY headcount DESC
        """)
        department_headcount = cursor.fetchall()
        metrics['department_labels'] = [row[0] for row in department_headcount]
        metrics['department_data'] = [row[1] for row in department_headcount]
    
    # 2. Salary distribution by department
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT d.department_name, 
                   ROUND(AVG(jsr.salary_range), 2) as avg_salary,
                   ROUND(MAX(jsr.salary_range), 2) as max_salary,
                   ROUND(MIN(jsr.salary_range), 2) as min_salary
            FROM payroll_department d
            JOIN payroll_employee e ON d.department_id = e.department_id
            JOIN payroll_job j ON e.job_id = j.job_id
            JOIN payroll_jobsalaryrange jsr ON j.job_id = jsr.job_id
            GROUP BY d.department_id, d.department_name
            ORDER BY avg_salary DESC
        """)
        salary_metrics = cursor.fetchall()
        metrics['salary_metrics'] = []
        for row in salary_metrics:
            metrics['salary_metrics'].append({
                'department': row[0],
                'avg_salary': row[1],
                'max_salary': row[2],
                'min_salary': row[3]
            })
    
    # 3. Attendance and overtime metrics (last 30 days)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                d.department_name,
                COUNT(DISTINCT a.employee_id) as employees_with_attendance,
                ROUND(AVG(a.hours_worked), 2) as avg_hours_worked,
                ROUND(SUM(a.overtime_hours), 2) as total_overtime_hours
            FROM payroll_attendance a
            JOIN payroll_employee e ON a.employee_id = e.employee_id
            JOIN payroll_department d ON e.department_id = d.department_id
            WHERE a.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY d.department_id, d.department_name
            ORDER BY total_overtime_hours DESC
        """)
        attendance_metrics = cursor.fetchall()
        metrics['attendance_metrics'] = []
        for row in attendance_metrics:
            metrics['attendance_metrics'].append({
                'department': row[0],
                'employees_with_attendance': row[1],
                'avg_hours_worked': row[2],
                'total_overtime_hours': row[3]
            })
    
    # 4. Leave statistics
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                leave_type,
                COUNT(*) as leave_count,
                SUM(DATEDIFF(end_date, start_date) + 1) as total_days
            FROM payroll_leave
            WHERE start_date >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
            GROUP BY leave_type
            ORDER BY total_days DESC
        """)
        leave_metrics = cursor.fetchall()
        metrics['leave_labels'] = [row[0] for row in leave_metrics]
        metrics['leave_count'] = [row[1] for row in leave_metrics]
        metrics['leave_days'] = [row[2] for row in leave_metrics]
    
    # 5. Financial overview
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                SUM(jsr.salary_range) as total_base_salary,
                SUM(p.allowances) as total_allowances,
                SUM(b.bonus_amount) as total_bonuses,
                SUM(d.tax_amount) as total_tax,
                SUM(d.other_deductions) as total_other_deductions
            FROM payroll_employee e
            JOIN payroll_job j ON e.job_id = j.job_id
            JOIN payroll_jobsalaryrange jsr ON j.job_id = jsr.job_id
            LEFT JOIN payroll_payroll p ON e.employee_id = p.employee_id
            LEFT JOIN payroll_bonus b ON p.payroll_id = b.payroll_id
            LEFT JOIN payroll_deduction d ON p.payroll_id = d.payroll_id
        """)
        finance = cursor.fetchone()
        metrics['finance'] = {
            'total_base_salary': finance[0] or 0,
            'total_allowances': finance[1] or 0,
            'total_bonuses': finance[2] or 0,
            'total_tax': finance[3] or 0,
            'total_other_deductions': finance[4] or 0,
            'total_cost': (finance[0] or 0) + (finance[1] or 0) + (finance[2] or 0)
        }
    
    # 6. Recent joiners (last 90 days)
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                e.name, 
                d.department_name, 
                j.job_title,
                e.date_joined
            FROM payroll_employee e
            JOIN payroll_department d ON e.department_id = d.department_id
            JOIN payroll_job j ON e.job_id = j.job_id
            WHERE e.date_joined >= DATE_SUB(CURDATE(), INTERVAL 90 DAY)
            ORDER BY e.date_joined DESC
            LIMIT 5
        """)
        recent_joiners = cursor.fetchall()
        metrics['recent_joiners'] = []
        for row in recent_joiners:
            metrics['recent_joiners'].append({
                'name': row[0],
                'department': row[1],
                'job_title': row[2],
                'date_joined': row[3]
            })
    
    return render(request, 'hr/metrics_dashboard.html', {'metrics': metrics})
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
        cursor.execute("SELECT department_id, department_name FROM payroll_department where department_name != 'HR'")
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
def update_payscales(request):
    # Ensure only HR users can access this page
    if not request.user.is_authenticated or request.user.role != 'HR':
        messages.error(request, "Access denied. Only HR users can access this page.")
        return redirect('login')
    
    # Fetch all departments except HR department
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT department_id, department_name
            FROM payroll_department
            WHERE department_name != 'HR'
            """
        )
        departments = cursor.fetchall()
    
    selected_department = None
    selected_department_name = None
    jobs = []
    
    # Handle department selection
    if request.method == 'POST' and request.POST.get('action') == 'select_department':
        selected_department = request.POST.get('department_id')
        
        # Get department name for display
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT department_name FROM payroll_department WHERE department_id = %s",
                [selected_department]
            )
            dept_result = cursor.fetchone()
            if dept_result:
                selected_department_name = dept_result[0]
        
        # Get jobs in the selected department
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT j.job_id, j.job_title, jsr.salary_range
                FROM payroll_job j
                JOIN payroll_jobsalaryrange jsr ON j.job_id = jsr.job_id
                JOIN payroll_employee e ON j.job_id = e.job_id
                WHERE e.department_id = %s
                GROUP BY j.job_id, j.job_title, jsr.salary_range
                """,
                [selected_department]
            )
            job_rows = cursor.fetchall()
            
            jobs = [
                {
                    'job_id': row[0],
                    'job_title': row[1],
                    'salary_range': row[2]
                }
                for row in job_rows
            ]
    
    # Handle salary update
    if request.method == 'POST' and request.POST.get('action') == 'update_salary':
        job_id = request.POST.get('job_id')
        salary_range = request.POST.get('salary_range')
        selected_department = request.POST.get('department_id')  # Keep the department selected
        
        # Update the salary range
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE payroll_jobsalaryrange
                SET salary_range = %s
                WHERE job_id = %s
                """,
                [salary_range, job_id]
            )
        
        # Get job title for the success message
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT job_title FROM payroll_job WHERE job_id = %s",
                [job_id]
            )
            job_title = cursor.fetchone()[0]
        
        messages.success(request, f"Salary updated successfully for {job_title} to ₹{salary_range}")
        
        # Get department name for display
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT department_name FROM payroll_department WHERE department_id = %s",
                [selected_department]
            )
            dept_result = cursor.fetchone()
            if dept_result:
                selected_department_name = dept_result[0]
        
        # Get updated jobs in the selected department
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT j.job_id, j.job_title, jsr.salary_range
                FROM payroll_job j
                JOIN payroll_jobsalaryrange jsr ON j.job_id = jsr.job_id
                JOIN payroll_employee e ON j.job_id = e.job_id
                WHERE e.department_id = %s
                GROUP BY j.job_id, j.job_title, jsr.salary_range
                """,
                [selected_department]
            )
            job_rows = cursor.fetchall()
            
            jobs = [
                {
                    'job_id': row[0],
                    'job_title': row[1],
                    'salary_range': row[2]
                }
                for row in job_rows
            ]

    return render(request, 'hr/update_payscales.html', {
        'departments': departments,
        'jobs': jobs,
        'selected_department': selected_department,
        'selected_department_name': selected_department_name
    })



@login_required
def generate_reports(request):
    # Ensure only HR users can access this page
    if not request.user.is_authenticated or request.user.role != 'HR':
        messages.error(request, "Access denied. Only HR users can access this page.")
        return redirect('login')
    
    # Initialize variables
    departments = []
    report_data = None
    report_type = None
    start_date = None
    end_date = None
    department_id = None
    report_format = 'html'  # Default format
    
    # Fetch all departments for the filter dropdown
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT department_id, department_name 
            FROM payroll_department
            WHERE department_name != 'HR'
        """)
        departments = cursor.fetchall()
    
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        department_id = request.POST.get('department_id')
        report_format = request.POST.get('report_format', 'html')
        
        # Generate report based on type
        if report_type == 'payroll':
            report_data = generate_payroll_report(start_date, end_date, department_id)
        elif report_type == 'attendance':
            report_data = generate_attendance_report(start_date, end_date, department_id)
        elif report_type == 'leave':
            report_data = generate_leave_report(start_date, end_date, department_id)
        elif report_type == 'tax':
            report_data = generate_tax_report(start_date, end_date, department_id)
        
        # Handle different export formats
        if report_format == 'pdf' and report_data:
            return generate_pdf(report_data, report_type)
        elif report_format == 'excel' and report_data:
            return generate_excel(report_data, report_type)
        elif report_format == 'csv' and report_data:
            return generate_csv(report_data, report_type)
    
    context = {
        'departments': departments,
        'report_data': report_data,
        'report_type': report_type,
        'start_date': start_date,
        'end_date': end_date,
        'department_id': department_id,
        'report_format': report_format  
    }
    
    return render(request, 'hr/generate_reports.html', context)
def generate_pdf(report_data, report_type):
    """Generate PDF version of the report"""
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF object, using the BytesIO object as its "file"
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    
    # Get the standard stylesheet
    styles = getSampleStyleSheet()
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Add report title
    title_style = styles['Heading1']
    title = Paragraph(f"{report_data['title']} ({report_data['period']})", title_style)
    elements.append(title)
    
    # Extract column headers
    headers = [col['name'] for col in report_data['columns']]
    
    # Prepare data for table
    data_table = [headers]
    for row in report_data['data']:
        data_table.append(row)
    
    # Add totals row if exists
    if 'totals' in report_data:
        totals_row = ['Totals'] * 3
        totals_row.extend(report_data['totals'])
        data_table.append(totals_row)
    
    # Create the table
    table = Table(data_table)
    
    # Add style to table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    
    # Add style to totals row if exists
    if 'totals' in report_data:
        style.add('BACKGROUND', (0, -1), (-1, -1), colors.grey)
        style.add('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke)
        style.add('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
    
    table.setStyle(style)
    
    # Add table to elements
    elements.append(table)
    
    # Build the PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create the HTTP response with PDF data
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.pdf"'
    response.write(pdf)
    
    return response

def generate_excel(report_data, report_type):
    """Generate Excel version of the report"""
    import xlwt
    from io import BytesIO
    
    # Create a workbook and add a worksheet
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet(report_type)
    
    # Define styles
    header_style = xlwt.easyxf('font: bold on; align: horiz center; pattern: pattern solid, fore_colour gray25;')
    totals_style = xlwt.easyxf('font: bold on; align: horiz center; pattern: pattern solid, fore_colour gray25;')
    cell_style = xlwt.easyxf('align: horiz center;')
    
    # Write headers
    for col_idx, column in enumerate(report_data['columns']):
        ws.write(0, col_idx, column['name'], header_style)
    
    # Write data
    for row_idx, row in enumerate(report_data['data'], 1):
        for col_idx, cell_value in enumerate(row):
            ws.write(row_idx, col_idx, cell_value, cell_style)
    
    # Write totals if they exist
    if 'totals' in report_data:
        totals_row = len(report_data['data']) + 1
        ws.write(totals_row, 0, 'Totals', totals_style)
        ws.write(totals_row, 1, '', totals_style)
        ws.write(totals_row, 2, '', totals_style)
        
        for col_idx, total in enumerate(report_data['totals'], 3):
            ws.write(totals_row, col_idx, total, totals_style)
    
    # Save the workbook to a BytesIO object
    output = BytesIO()
    wb.save(output)
    
    # Create the HTTP response
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.xls"'
    response.write(output.getvalue())
    
    return response
def generate_csv(report_data, report_type):
    """Generate CSV version of the report"""
    import csv
    
    # Create the HttpResponse with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow([column['name'] for column in report_data['columns']])
    
    # Write data rows
    for row in report_data['data']:
        writer.writerow(row)
    
    # Write totals row if exists
    if 'totals' in report_data:
        totals_row = ['Totals', '', ''] + report_data['totals']
        writer.writerow(totals_row)
    
    return response
def generate_payroll_report(start_date, end_date, department_id):
    """Generate payroll report with detailed salary, allowances, bonuses and deductions"""
    with connection.cursor() as cursor:
        query = """
            SELECT 
                d.department_name,
                e.name as employee_name,
                j.job_title,
                jsr.salary_range as base_salary,
                COALESCE(p.allowances, 0) as allowances,
                COALESCE(b.bonus_amount, 0) as bonus_amount,
                COALESCE(jsr.salary_range, 0) + COALESCE(p.allowances, 0) + COALESCE(b.bonus_amount, 0) as gross_pay,
                COALESCE(ded.tax_amount, 0) as tax,
                COALESCE(ded.other_deductions, 0) as other_deductions,
                COALESCE(jsr.salary_range, 0) + COALESCE(p.allowances, 0) + COALESCE(b.bonus_amount, 0) - 
                COALESCE(ded.tax_amount, 0) - COALESCE(ded.other_deductions, 0) as net_pay
            FROM 
                payroll_employee e
                JOIN payroll_department d ON e.department_id = d.department_id
                JOIN payroll_job j ON e.job_id = j.job_id
                JOIN payroll_jobsalaryrange jsr ON j.job_id = jsr.job_id
                LEFT JOIN payroll_payroll p ON e.employee_id = p.employee_id
                LEFT JOIN payroll_bonus b ON p.payroll_id = b.payroll_id
                LEFT JOIN payroll_deduction ded ON p.payroll_id = ded.payroll_id
            WHERE 1=1
        """
        params = []
        
        if department_id:
            query += " AND e.department_id = %s"
            params.append(department_id)
        
        query += " ORDER BY d.department_name, e.name"
        
        cursor.execute(query, params)
        data = cursor.fetchall()  # Fetch data only once
        
        return {
            'title': 'Payroll Summary Report',
            'period': f"{start_date} to {end_date}",
            'columns': [
                {'name': 'Department', 'width': '15%'},
                {'name': 'Employee', 'width': '15%'},
                {'name': 'Position', 'width': '15%'},
                {'name': 'Base Salary', 'width': '10%'},
                {'name': 'Allowances', 'width': '10%'},
                {'name': 'Bonus', 'width': '10%'},
                {'name': 'Gross Pay', 'width': '10%'},
                {'name': 'Tax', 'width': '5%'},
                {'name': 'Deductions', 'width': '5%'},
                {'name': 'Net Pay', 'width': '10%'}
            ],
            'data': data,
            'totals': calculate_payroll_totals(data)
        }

def generate_attendance_report(start_date, end_date, department_id):
    """Generate attendance report with hours worked and overtime"""
    with connection.cursor() as cursor:
        query = """
            SELECT 
                d.department_name,
                e.name as employee_name,
                COUNT(DISTINCT a.date) as days_present,
                ROUND(SUM(a.hours_worked), 2) as total_hours,
                ROUND(AVG(a.hours_worked), 2) as avg_hours_per_day,
                ROUND(SUM(a.overtime_hours), 2) as total_overtime,
                COUNT(CASE WHEN a.leave_status IS NOT NULL AND a.leave_status != 'Present' THEN 1 END) as leave_days
            FROM 
                payroll_employee e
                JOIN payroll_department d ON e.department_id = d.department_id
                LEFT JOIN payroll_attendance a ON e.employee_id = a.employee_id
            WHERE 
                a.date BETWEEN %s AND %s
        """
        params = [start_date, end_date]
        
        if department_id:
            query += " AND e.department_id = %s"
            params.append(department_id)
        
        query += " GROUP BY d.department_name, e.name ORDER BY d.department_name, e.name"
        
        cursor.execute(query, params)
        data = cursor.fetchall()
        
        return {
            'title': 'Attendance Report',
            'period': f"{start_date} to {end_date}",
            'columns': [
                {'name': 'Department', 'width': '20%'},
                {'name': 'Employee', 'width': '20%'},
                {'name': 'Days Present', 'width': '10%'},
                {'name': 'Total Hours', 'width': '10%'},
                {'name': 'Avg Hours/Day', 'width': '15%'},
                {'name': 'Overtime Hours', 'width': '15%'},
                {'name': 'Leave Days', 'width': '10%'}
            ],
            'data': data
        }

def generate_leave_report(start_date, end_date, department_id):
    """Generate detailed leave report"""
    with connection.cursor() as cursor:
        query = """
            SELECT 
                d.department_name,
                e.name as employee_name,
                l.leave_type,
                l.start_date,
                l.end_date,
                DATEDIFF(l.end_date, l.start_date) + 1 as days_taken,
                l.status
            FROM 
                payroll_leave l
                JOIN payroll_employee e ON l.employee_id = e.employee_id
                JOIN payroll_department d ON e.department_id = d.department_id
            WHERE 
                (l.start_date BETWEEN %s AND %s OR l.end_date BETWEEN %s AND %s)
        """
        params = [start_date, end_date, start_date, end_date]
        
        if department_id:
            query += " AND e.department_id = %s"
            params.append(department_id)
        
        query += " ORDER BY d.department_name, e.name, l.start_date"
        
        cursor.execute(query, params)
        data = cursor.fetchall()
        
        return {
            'title': 'Leave Report',
            'period': f"{start_date} to {end_date}",
            'columns': [
                {'name': 'Department', 'width': '15%'},
                {'name': 'Employee', 'width': '15%'},
                {'name': 'Leave Type', 'width': '15%'},
                {'name': 'Start Date', 'width': '15%'},
                {'name': 'End Date', 'width': '15%'},
                {'name': 'Days', 'width': '10%'},
                {'name': 'Status', 'width': '15%'}
            ],
            'data': data
        }

def generate_tax_report(start_date, end_date, department_id):
    """Generate tax deductions report"""
    with connection.cursor() as cursor:
        query = """
            SELECT 
                dept.department_name,
                e.name,
                j.job_title,
                COALESCE(jsr.salary_range, 0) * 12 as annual_salary,
                COALESCE(deduct.tax_amount, 0) as monthly_tax,
                COALESCE(deduct.tax_amount, 0) * 12 as annual_tax,
                CASE 
                    WHEN COALESCE(jsr.salary_range, 0) > 0 
                    THEN ROUND((COALESCE(deduct.tax_amount, 0) * 12) / (COALESCE(jsr.salary_range, 0) * 12) * 100, 2)
                    ELSE 0
                END as effective_tax_rate
            FROM 
                payroll_employee e
                JOIN payroll_department dept ON e.department_id = dept.department_id
                JOIN payroll_job j ON e.job_id = j.job_id
                JOIN payroll_jobsalaryrange jsr ON j.job_id = jsr.job_id
                LEFT JOIN payroll_payroll p ON e.employee_id = p.employee_id
                LEFT JOIN payroll_deduction deduct ON p.payroll_id = deduct.payroll_id
            WHERE 1=1
        """
        params = []
        
        if department_id:
            query += " AND e.department_id = %s"
            params.append(department_id)
        
        query += " ORDER BY dept.department_name, monthly_tax DESC"
        
        cursor.execute(query, params)
        data = cursor.fetchall()
        
        return {
            'title': 'Tax Deduction Report',
            'period': f"{start_date} to {end_date}",
            'columns': [
                {'name': 'Department', 'width': '15%'},
                {'name': 'Employee', 'width': '15%'},
                {'name': 'Position', 'width': '15%'},
                {'name': 'Annual Salary', 'width': '15%'},
                {'name': 'Monthly Tax', 'width': '15%'},
                {'name': 'Annual Tax', 'width': '15%'},
                {'name': 'Effective Rate', 'width': '10%'}
            ],
            'data': data
        }


def calculate_payroll_totals(data):
    """
    Calculate column totals for payroll report
    Returns a list of totals for: base_salary, allowances, bonus, gross_pay, tax, deductions, net_pay
    """
    # Return empty list if no data
    if not data:
        return [0, 0, 0, 0, 0, 0, 0]
    
    # Initialize totals (we don't sum department, employee name, and job title)
    base_salary_total = 0
    allowances_total = 0
    bonus_total = 0
    gross_pay_total = 0
    tax_total = 0
    deductions_total = 0
    net_pay_total = 0
    
    # Sum each column
    for row in data:
        # Index 3 is base_salary, 4 is allowances, 5 is bonus, etc.
        base_salary_total += float(row[3] or 0)
        allowances_total += float(row[4] or 0)
        bonus_total += float(row[5] or 0)
        gross_pay_total += float(row[6] or 0)
        tax_total += float(row[7] or 0)
        deductions_total += float(row[8] or 0)
        net_pay_total += float(row[9] or 0)
    
    # Return totals as a list in the same order as columns
    return [
        round(base_salary_total, 2),
        round(allowances_total, 2),
        round(bonus_total, 2),
        round(gross_pay_total, 2),
        round(tax_total, 2),
        round(deductions_total, 2),
        round(net_pay_total, 2)
    ]


@login_required
def attendance_details(request):
    # Ensure only HR users can access this page
    if not request.user.is_authenticated or request.user.role != 'HR':
        messages.error(request, "Access denied. Only HR users can access this page.")
        return redirect('login')
    
    # Initialize variables
    departments = []
    employees = []
    attendance_records = []
    employee_details = None
    
    # Get filter parameters
    department_id = request.GET.get('department_id', '')
    employee_id = request.GET.get('employee_id', '')
    
    # Date range (default to current month)
    today = datetime.today()
    start_date = request.GET.get('start_date', (today.replace(day=1)).strftime('%Y-%m-%d'))
    
    # If end_date not provided, set to last day of month
    if request.GET.get('end_date'):
        end_date = request.GET.get('end_date')
    else:
        last_day = calendar.monthrange(today.year, today.month)[1]
        end_date = (today.replace(day=last_day)).strftime('%Y-%m-%d')
    
    # Fetch all departments for filter dropdown
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT department_id, department_name
            FROM payroll_department
            ORDER BY department_name
        """)
        departments = cursor.fetchall()
    
    # If department selected, fetch employees in that department
    if department_id:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT employee_id, name
                FROM payroll_employee
                WHERE department_id = %s
                ORDER BY name
            """, [department_id])
            employees = cursor.fetchall()
    
    # Build query conditions based on filters
    conditions = []
    params = [start_date, end_date]
    
    if employee_id:
        conditions.append("e.employee_id = %s")  # Fixed: Use e.employee_id instead of a.employee_id
        params.append(employee_id)
        
        # Get employee details if specific employee selected
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    e.name, 
                    d.department_name, 
                    j.job_title,
                    e.date_joined,
                    e.email,
                    e.contact
                FROM 
                    payroll_employee e
                    JOIN payroll_department d ON e.department_id = d.department_id
                    JOIN payroll_job j ON e.job_id = j.job_id
                WHERE e.employee_id = %s
            """, [employee_id])
            employee_details = cursor.fetchone()
            
    elif department_id:
        conditions.append("e.department_id = %s")
        params.append(department_id)
    
    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "AND " + where_clause
    
    try:
        # Debug query to check hours_worked values
        if employee_id:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT hours_worked 
                    FROM payroll_attendance 
                    WHERE employee_id = %s AND date BETWEEN %s AND %s
                    LIMIT 5
                """, [employee_id, start_date, end_date])
                hours_sample = cursor.fetchall()
                if hours_sample:
                    print(f"Sample hours_worked values: {hours_sample}")
        
        # Fetch attendance records with filters applied - Fixed status calculation
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    d.department_name,
                    e.employee_id,
                    e.name as employee_name,
                    j.job_title,
                    DATE_FORMAT(a.date, '%%Y-%%m-%%d') as date,
                    DAYNAME(a.date) as day_name,
                    a.hours_worked,
                    a.overtime_hours,
                    a.leave_status,
                    CASE 
                        WHEN a.leave_status = 'Sick' OR a.leave_status = 'Vacation' OR a.leave_status = 'Personal' THEN a.leave_status
                        WHEN COALESCE(a.hours_worked, 0) < 1 THEN 'Absent'
                        ELSE 'Present'
                    END AS attendance_status
                FROM 
                    payroll_employee e
                    JOIN payroll_department d ON e.department_id = d.department_id
                    JOIN payroll_job j ON e.job_id = j.job_id
                    LEFT JOIN payroll_attendance a ON e.employee_id = a.employee_id AND a.date BETWEEN %s AND %s
                WHERE 
                    a.date IS NOT NULL
                """ + (f" {where_clause}" if where_clause else "") + """
                ORDER BY 
                    a.date DESC, d.department_name, e.name
                LIMIT 500
            """, params)
            attendance_records = cursor.fetchall()
            
            # Debug info
            if not attendance_records and employee_id:
                # Check if we have any attendance records for this employee
                cursor.execute("""
                    SELECT COUNT(*) FROM payroll_attendance 
                    WHERE employee_id = %s
                """, [employee_id])
                count = cursor.fetchone()[0]
                print(f"Total attendance records for employee {employee_id}: {count}")
    
    except Exception as e:
        messages.error(request, f"Database error: {str(e)}")
        print(f"Exception details: {e}")
    
    context = {
        'departments': departments,
        'employees': employees,
        'attendance_records': attendance_records,
        'employee_details': employee_details,
        'selected_department': department_id,
        'selected_employee': employee_id,
        'start_date': start_date,
        'end_date': end_date,
        'date_range': f"{start_date} to {end_date}"
    }
    
    return render(request, 'hr/attendance_details.html', context)


@login_required
def approve_leave_requests(request):
    # Ensure only HR users can access this page
    if not request.user.is_authenticated or request.user.role != 'HR':
        messages.error(request, "Access denied. Only HR users can access this page.")
        return redirect('login')
    
    # Initialize variables
    pending_requests = []
    approved_requests = []
    rejected_requests = []
    
    # Handle approval/rejection action
    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        action = request.POST.get('action')
        
        if leave_id and action in ['Approved', 'Rejected']:
            try:
                with connection.cursor() as cursor:
                    # Get leave details before updating
                    cursor.execute("""
                        SELECT employee_id, leave_type, start_date, end_date
                        FROM payroll_leave
                        WHERE leave_id = %s
                    """, [leave_id])
                    leave_details = cursor.fetchone()
                    
                    if leave_details:
                        # Just update the leave status - trigger will handle attendance records
                        cursor.execute("""
                            UPDATE payroll_leave
                            SET status = %s
                            WHERE leave_id = %s
                        """, [action, leave_id])
                
                messages.success(request, f"Leave request {action.lower()} successfully!")
            except Exception as e:
                messages.error(request, f"Error processing request: {str(e)}")
    
    try:
        # Fetch all pending leave requests
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    l.leave_id,
                    e.employee_id,
                    e.name as employee_name,
                    d.department_name,
                    l.leave_type,
                    l.start_date,
                    l.end_date,
                    DATEDIFF(l.end_date, l.start_date) + 1 as days_requested,
                    l.status
                FROM 
                    payroll_leave l
                    JOIN payroll_employee e ON l.employee_id = e.employee_id
                    JOIN payroll_department d ON e.department_id = d.department_id
                WHERE 
                    l.status = 'Pending'
                ORDER BY 
                    l.start_date ASC
            """)
            pending_requests = cursor.fetchall()
            
            # Fetch recently approved requests
            cursor.execute("""
                SELECT 
                    l.leave_id,
                    e.employee_id,
                    e.name as employee_name,
                    d.department_name,
                    l.leave_type,
                    l.start_date,
                    l.end_date,
                    DATEDIFF(l.end_date, l.start_date) + 1 as days_requested,
                    l.status
                FROM 
                    payroll_leave l
                    JOIN payroll_employee e ON l.employee_id = e.employee_id
                    JOIN payroll_department d ON e.department_id = d.department_id
                WHERE 
                    l.status = 'Approved'
                ORDER BY 
                    l.start_date DESC
                LIMIT 10
            """)
            approved_requests = cursor.fetchall()
            
            # Fetch recently rejected requests
            cursor.execute("""
                SELECT 
                    l.leave_id,
                    e.employee_id,
                    e.name as employee_name,
                    d.department_name,
                    l.leave_type,
                    l.start_date,
                    l.end_date,
                    DATEDIFF(l.end_date, l.start_date) + 1 as days_requested,
                    l.status
                FROM 
                    payroll_leave l
                    JOIN payroll_employee e ON l.employee_id = e.employee_id
                    JOIN payroll_department d ON e.department_id = d.department_id
                WHERE 
                    l.status = 'Rejected'
                ORDER BY 
                    l.start_date DESC
                LIMIT 10
            """)
            rejected_requests = cursor.fetchall()
    except Exception as e:
        messages.error(request, f"Database error: {str(e)}")
    
    context = {
        'pending_requests': pending_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests
    }
    
    return render(request, 'hr/approve_leaves.html', context)


@login_required
def manage_employees1(request):
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
    current_manager = None
    
    # Handle manager assignment
    if request.method == 'POST' and request.POST.get('action') == 'assign_manager':
        employee_id = request.POST.get('employee_id')
        department_id = request.POST.get('department_id')
        
        try:
            # Assign employee as department manager
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE payroll_department SET manager_id = %s WHERE department_id = %s",
                    [employee_id, department_id]
                )
            
            # Get department and employee name for success message
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT department_name FROM payroll_department WHERE department_id = %s",
                    [department_id]
                )
                dept_name = cursor.fetchone()[0]
                
                cursor.execute(
                    "SELECT name FROM payroll_employee WHERE employee_id = %s",
                    [employee_id]
                )
                emp_name = cursor.fetchone()[0]
                
            messages.success(request, f"{emp_name} has been assigned as manager of the {dept_name} department.")
            selected_department = department_id
        except Exception as e:
            messages.error(request, f"Error assigning manager: {str(e)}")
            selected_department = department_id

    # If a department is selected, fetch employees in that department
    if request.method == 'POST' and 'department_id' in request.POST and request.POST.get('action') == 'view_employees':
        selected_department = request.POST.get('department_id')
    
    if selected_department:
        # Get current manager for the selected department
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT d.manager_id, e.name 
                FROM payroll_department d
                LEFT JOIN payroll_employee e ON d.manager_id = e.employee_id
                WHERE d.department_id = %s
                """, [selected_department]
            )
            manager_info = cursor.fetchone()
            if manager_info and manager_info[0]:
                current_manager = {"id": manager_info[0], "name": manager_info[1]}
        
        # Get employees in the department
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT e.employee_id, e.name, e.contact, e.email, j.job_title, d.department_name,
                       COALESCE(b.bonus_amount, 0) AS bonus,
                       CASE WHEN d.manager_id = e.employee_id THEN 'Yes' ELSE 'No' END as is_manager
                FROM payroll_employee e
                LEFT JOIN payroll_job j ON e.job_id = j.job_id
                LEFT JOIN payroll_department d ON e.department_id = d.department_id
                LEFT JOIN payroll_payroll p ON e.employee_id = p.employee_id
                LEFT JOIN payroll_bonus b ON b.payroll_id = p.payroll_id
                WHERE e.department_id = %s
                ORDER BY e.name
                """, [selected_department]
            )
            employees = cursor.fetchall()

    # Handle reassignment or bonus update
    if request.method == 'POST' and request.POST.get('action') == 'update_employee':
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
        selected_department = request.POST.get('department_id', selected_department)

    # Fetch all jobs for the dropdown
    with connection.cursor() as cursor:
        cursor.execute("SELECT job_id, job_title FROM payroll_job")
        jobs = cursor.fetchall()

    return render(request, 'hr/manage_employee.html', {
        'departments': departments,
        'employees': employees,
        'jobs': jobs,
        'selected_department': selected_department,
        'current_manager': current_manager
    })


@login_required
def hr_dashboard(request):
    # Get stats for dashboard
    with connection.cursor() as cursor:
        # Total employees
        cursor.execute("SELECT COUNT(*) FROM payroll_employee")
        total_employees = cursor.fetchone()[0]
        
        # Departments
        cursor.execute("SELECT COUNT(*) FROM payroll_department")
        departments = cursor.fetchone()[0]
        
        # Pending leave requests
        cursor.execute("SELECT COUNT(*) FROM payroll_leave WHERE status = 'Pending'")
        pending_leave = cursor.fetchone()[0]
        
        # Pending payments

       
        cursor.execute("""
            SELECT COUNT(*) 
            FROM payroll_payroll p
            LEFT JOIN payroll_payment pm ON p.payroll_id = pm.payroll_id
            WHERE pm.payment_id IS NULL
        """)
       
        pending_payments = cursor.fetchone()[0]
            
    context = {
        'stats': {
            'total_employees': total_employees,
            'departments': departments,
            'pending_leave': pending_leave,
            'pending_payments': pending_payments,
        },
        
    }
    
    return render(request, 'hr/dashboard.html', context)




def generate_bank_account(employee_id, payroll_id, payment_id):#helper function
    """Generate a 12-digit bank account number from IDs"""
    # Combine the IDs and pad with zeros to make it 12 digits
    combined = f"{employee_id}{payroll_id}{payment_id}"
    padded = combined.zfill(12)  # Ensure it's 12 digits with leading zeros
    
    # If longer than 12 digits (unlikely but possible with large IDs), truncate
    return padded[-12:]

@login_required
def salary_disbursement(request):
    if request.method == 'POST':
        payroll_id = request.POST.get('payroll_id')
        payment_mode = request.POST.get('payment_mode')

        bonus_amount = request.POST.get('bonus_amount', 0)
        
        # Validate required fields
        if not (payroll_id and payment_mode):
            messages.error(request, "Payment mode required.")
            return redirect('salary_disbursement')
            
        try:
            with connection.cursor() as cursor:
                # Check if payment already exists
                cursor.execute(
                    "SELECT payment_id FROM payroll_payment WHERE payroll_id = %s",
                    [payroll_id]
                )
                if cursor.fetchone():
                    messages.error(request, "Payment for this payroll has already been processed.")
                    return redirect('salary_disbursement')
                
                # Get employee_id for the payroll
                cursor.execute(
                    "SELECT employee_id FROM payroll_payroll WHERE payroll_id = %s",
                    [payroll_id]
                )
                employee_id = cursor.fetchone()[0]
                
                # Update bonus if provided
                if bonus_amount:
                    # Check if bonus record exists
                    cursor.execute(
                        "SELECT bonus_id FROM payroll_bonus WHERE payroll_id = %s",
                        [payroll_id]
                    )
                    bonus_record = cursor.fetchone()
                    
                    if bonus_record:
                        # Update existing bonus
                        cursor.execute(
                            "UPDATE payroll_bonus SET bonus_amount = %s WHERE payroll_id = %s",
                            [bonus_amount, payroll_id]
                        )
                    else:
                        # Create new bonus record
                        cursor.execute(
                            "INSERT INTO payroll_bonus (payroll_id, bonus_amount) VALUES (%s, %s)",
                            [payroll_id, bonus_amount]
                        )
                
                # Create payment record
                cursor.execute(
                    "INSERT INTO payroll_payment (payroll_id) VALUES (%s)",
                    [payroll_id]
                )
                
                # Get the newly created payment_id
                payment_id = cursor.lastrowid
                
                # Generate bank account number
                transaction_id= bank_account = generate_bank_account(employee_id, payroll_id, payment_id)
                
                # Create payment detail record
                cursor.execute(
                    """
                    INSERT INTO payroll_paymentdetail 
                    (payment_id, payment_mode, transaction_id, bank_account) 
                    VALUES (%s, %s, %s, %s)
                    """,
                    [payment_id, payment_mode, transaction_id, bank_account]
                )
                
                messages.success(request, f"Payment processed successfully. Bank account: {bank_account}")
                return redirect('salary_disbursement')
                
        except Exception as e:
            messages.error(request, f"Error processing payment: {str(e)}")
            return redirect('salary_disbursement')
    
    # Get pending payrolls
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                distinct p.payroll_id, 
                e.employee_id,
                e.name, 
                d.department_name,
                j.job_title,
                jsr.salary_range,
                p.allowances,
                COALESCE(b.bonus_amount, 0) as bonus_amount,
                COALESCE(deduct.tax_amount, 0) as tax_amount,
                COALESCE(deduct.other_deductions, 0) as other_deductions
            FROM payroll_payroll p
            JOIN payroll_employee e ON p.employee_id = e.employee_id
            JOIN payroll_job j ON e.job_id = j.job_id
            JOIN payroll_department d ON e.department_id = d.department_id
            JOIN payroll_jobsalaryrange jsr ON j.job_id = jsr.job_id
            LEFT JOIN payroll_bonus b ON p.payroll_id = b.payroll_id
            LEFT JOIN payroll_deduction deduct ON p.payroll_id = deduct.payroll_id
            LEFT JOIN payroll_payment pm ON p.payroll_id = pm.payroll_id
            WHERE pm.payment_id IS NULL
            ORDER BY p.payroll_id DESC
            """
        )
        pending_payrolls = cursor.fetchall()
    
    # Format payroll data for display
    payrolls = []
    for record in pending_payrolls:
        payroll_id = record[0]
        employee_id = record[1]
        employee_name = record[2]
        department = record[3]
        job_title = record[4]
        base_salary = float(record[5]) if record[5] else 0
        allowances = float(record[6]) if record[6] else 0
        bonus = float(record[7]) if record[7] else 0
        tax = float(record[8]) if record[8] else 0
        other_deductions = float(record[9]) if record[9] else 0
        
        # Calculate gross and net pay
        gross_pay = base_salary + allowances + bonus
        total_deductions = tax + other_deductions
        net_pay = gross_pay - total_deductions
        
        payrolls.append({
            'payroll_id': payroll_id,
            'employee_id': employee_id,
            'employee_name': employee_name,
            'department': department,
            'job_title': job_title,
            'base_salary': base_salary,
            'allowances': allowances,
            'bonus': bonus,
            'tax': tax,
            'other_deductions': other_deductions,
            'gross_pay': gross_pay,
            'net_pay': net_pay
        })
    
    return render(request, 'hr/salary_disbursement.html', {'payrolls': payrolls})

@login_required
def payment_history(request):
    # Get processed payments
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT 
                distinct pm.payment_id,
                p.payroll_id, 
                e.name, 
                d.department_name,
                jsr.salary_range + p.allowances + COALESCE(b.bonus_amount, 0) - 
                    COALESCE(deduct.tax_amount, 0) - COALESCE(deduct.other_deductions, 0) as net_pay,
                pd.payment_mode,
                pd.transaction_id,
                pd.bank_account
            FROM payroll_payment pm
            JOIN payroll_payroll p ON pm.payroll_id = p.payroll_id
            JOIN payroll_employee e ON p.employee_id = e.employee_id
            JOIN payroll_job j ON e.job_id = j.job_id
            JOIN payroll_department d ON e.department_id = d.department_id
            JOIN payroll_jobsalaryrange jsr ON j.job_id = jsr.job_id
            LEFT JOIN payroll_bonus b ON p.payroll_id = b.payroll_id
            LEFT JOIN payroll_deduction deduct ON p.payroll_id = deduct.payroll_id
            LEFT JOIN payroll_paymentdetail pd ON pm.payment_id = pd.payment_id
            ORDER BY pm.payment_id DESC
            """
        )
        payment_records = cursor.fetchall()
    
    # Format payment data
    payments = []
    for record in payment_records:
        payment_id = record[0]
        payroll_id = record[1]
        employee_name = record[2]
        department = record[3]
        net_pay = float(record[4]) if record[4] else 0
        payment_mode = record[5]
        transaction_id = record[6]
        bank_account = record[7]
        
        payments.append({
            'payment_id': payment_id,
            'payroll_id': payroll_id,
            'employee_name': employee_name,
            'department': department,
            'net_pay': net_pay,
            'payment_mode': payment_mode,
            'transaction_id': transaction_id,
            'bank_account': bank_account
        })
    
    return render(request, 'hr/payment_history.html', {'payments': payments})

