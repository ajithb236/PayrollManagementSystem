# Description: This file contains the views for the accounts app.
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .models import CustomUser
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.decorators import login_required
from django.db import connection

class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = [('Employee', 'Employee'), ('HR', 'HR')] #2 different types of users.
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'role']

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        name = request.POST.get('name','').strip()
        contact = request.POST.get('contact','').strip()
        role_name = request.POST.get('role','').strip() # "Employee" or "HR"
        email_id = request.POST.get('email_id','').strip()
        if form.is_valid():
            user = form.save()  
            user.refresh_from_db()  # Update user instance
            
            with connection.cursor() as cursor:
                # Insert into Employee table
                cursor.execute(
                    "INSERT INTO payroll_Employee (user_id, name, contact,email) VALUES (%s, %s, %s, %s)",
                    [user.id, name, contact,email_id]
                )
                
                # Get employee ID
                cursor.execute("SELECT employee_id FROM payroll_Employee WHERE user_id = %s", [user.id])
                employee_id = cursor.fetchone()[0]

                # Assign HR role if selected
                if role_name == "HR":
                    print("HRR")
                    cursor.execute("SELECT role_id FROM payroll_Role WHERE role_name = 'HR'")
                    hr_role = cursor.fetchone()
                    if not hr_role:
                        cursor.execute("INSERT INTO payroll_Role (role_name) VALUES ('HR')")
                        cursor.execute("SELECT role_id FROM payroll_Role WHERE role_name = 'HR'")
                        hr_role = cursor.fetchone()
                    role_id = hr_role[0]
                    
                    # Assign HR role to employee
                    cursor.execute(
                        "INSERT INTO payroll_EmployeeRole (employee_id, role_id) VALUES (%s, %s)",
                        [employee_id, role_id]
                    )

                    # Ensure HR department exists
                    cursor.execute("SELECT department_id FROM payroll_Department WHERE department_name = 'HR'")
                    hr_department = cursor.fetchone()
                    if not hr_department:
                        cursor.execute("INSERT INTO payroll_Department (department_name) VALUES ('HR')")
                        cursor.execute("SELECT department_id FROM payroll_Department WHERE department_name = 'HR'")
                        hr_department = cursor.fetchone()

                    department_id = hr_department[0]
                    
                    # Update Employee table with HR department
                    cursor.execute(
                        "UPDATE payroll_Employee SET department_id = %s WHERE employee_id = %s",
                        [department_id, employee_id]
                    )

            login(request, user)
            return redirect('login')

    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})

from django.views.decorators.csrf import csrf_exempt
@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.role == 'HR':
                return redirect('hr_dashboard')  # Redirect HR to HR dashboard
            else:
                return redirect('employee_dashboard')  # Redirect Employee to Employee dashboard
        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid credentials'})

    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect("login")