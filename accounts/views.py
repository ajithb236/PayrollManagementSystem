# Description: This file contains the views for the accounts app.
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from .models import CustomUser
from django.contrib.auth.forms import UserCreationForm
from django import forms

class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = [('Employee', 'Employee'), ('HR', 'HR')] #2 different types of users.
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password1', 'password2', 'role']

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('login')  # Redirect after successful registration
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

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
