# Description: This file contains the views for the accounts app.
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .models import CustomUser
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.decorators import login_required
from django.db import connection
from datetime import datetime
from django.contrib import messages
from payroll.models import Payroll,Employee,Bonus,Deduction
class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = [('Employee', 'Employee'), ('HR', 'HR')] 
    role = forms.ChoiceField(choices=ROLE_CHOICES)
    name = forms.CharField(max_length=255, required=True)
    contact = forms.CharField(max_length=20, required=True)
    # Override the default email field to make it required
    email = forms.EmailField(
        max_length=255, 
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Enter your email address'})
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'role', 'name', 'contact']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add placeholders to default fields
        self.fields['username'].widget.attrs.update({'placeholder': 'Choose a unique username'})
        self.fields['name'].widget.attrs.update({'placeholder': 'Enter your full name'})
        self.fields['contact'].widget.attrs.update({'placeholder': 'Enter your contact number'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Create a strong password'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm your password'})


def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Create the user with form.save() to properly handle password hashing
            user = form.save()
            
            # Extract form fields using cleaned_data (validated data)
            name = form.cleaned_data.get('name', '')
            contact = form.cleaned_data.get('contact', '')
            email = form.cleaned_data.get('email', '')  # This is the correct field name now
            
            # Create the employee record using raw SQL
            with connection.cursor() as cursor:
                # Create employee record - this will trigger the MySQL trigger
                cursor.execute(
                    """INSERT INTO payroll_Employee 
                       (user_id, name, contact, email, date_joined) 
                       VALUES (%s, %s, %s, %s, %s)""",
                    [user.id, name, contact, email, datetime.now()]
                )
                
                # The trigger will automatically:
                # 1. Create the payroll record
                # 2. Create deduction and bonus records
                # 3. Set up HR role/department if needed
                
                # Update the last_login field for the user
                cursor.execute(
                    "UPDATE accounts_customuser SET last_login = NOW() WHERE id = %s",
                    [user.id]
                )
            
            messages.success(request, 'Registration successful! You can now log in.')
            login(request, user)
            return redirect('login')
        else:
            messages.error(request, 'Registration failed. Please fix the errors below.')
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
    messages.success(request, "Logged out successfully.")
    return redirect("login")