from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from payroll.models import Job  # Import Job from Payroll app
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
    # Logic to manage employees
    return render(request, 'hr/manage_employees.html')