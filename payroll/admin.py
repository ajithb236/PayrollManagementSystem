from django.contrib import admin

# Register your models here.
from .models import Department, Job, Employee, Payroll, Attendance, Leave, Deduction, Bonus, Payment, PaymentDetail,JobSalaryRange,Role,EmployeeRole

admin.site.register(Department)
admin.site.register(Job)
admin.site.register(Employee)
admin.site.register(Payroll)
admin.site.register(Attendance)
admin.site.register(Leave)
admin.site.register(Deduction)
admin.site.register(Bonus)
admin.site.register(Payment)
admin.site.register(PaymentDetail)
admin.site.register(JobSalaryRange)
admin.site.register(Role)
admin.site.register(EmployeeRole)