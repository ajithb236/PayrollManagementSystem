from django.db import models
from django.conf import settings



# Create your models here.
from django.db import models

class Department(models.Model):
    department_id = models.AutoField(primary_key=True)#int which increments automatically
    department_name = models.CharField(max_length=100)#varchar(100)
    manager_id = models.IntegerField(null=True, blank=True)#int

class Job(models.Model):
    job_id = models.AutoField(primary_key=True)
    job_title = models.CharField(max_length=100)

class JobSalaryRange(models.Model):
    job = models.OneToOneField(Job, on_delete=models.CASCADE)
    salary_range = models.DecimalField(max_digits=10, decimal_places=2)
class Employee(models.Model):
    employee_id = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Separate user details
    name = models.CharField(max_length=255,default='user')  # Added name
    contact = models.CharField(max_length=20,default=123456789)  # Added contact
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True, blank=True)  # Can be NULL until HR assigns it
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)  # Can be NULL
    email = models.EmailField(max_length=255,default='user@user.com')  # Added email field
    def __str__(self):
        return f"{self.name} ({self.user.username})"

class Role(models.Model):
    role_id = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True)  # 'Employee', 'HR'

class EmployeeRole(models.Model):  # Many-to-Many table for Employees and Roles
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)

class Payroll(models.Model):
    payroll_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    allowances = models.DecimalField(max_digits=10, decimal_places=2)

class Attendance(models.Model):
    attendance_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    hours_worked = models.DecimalField(max_digits=5, decimal_places=2)
    shift_type = models.CharField(max_length=50)
    leave_status = models.CharField(max_length=50)

class Leave(models.Model):
    leave_id = models.AutoField(primary_key=True)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    leave_type = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=50)

class Deduction(models.Model):
    deduction_id = models.AutoField(primary_key=True)
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2)
    other_deductions = models.DecimalField(max_digits=10, decimal_places=2)

class Bonus(models.Model):
    bonus_id = models.AutoField(primary_key=True)
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE)
    bonus_amount = models.DecimalField(max_digits=10, decimal_places=2)

class Payment(models.Model):
    payment_id = models.AutoField(primary_key=True)
    payroll = models.ForeignKey(Payroll, on_delete=models.CASCADE)

class PaymentDetail(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)
    payment_mode = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, unique=True)
    bank_account = models.CharField(max_length=100)
