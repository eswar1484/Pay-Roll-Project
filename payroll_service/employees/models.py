from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Manager(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    manager_id = models.CharField(max_length=100, unique=True)
    contact = models.CharField(max_length=15)

    def __str__(self):
        return self.name
    
class SalaryJobType(models.Model):
    job_title = models.CharField(max_length=255)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    deduction_money = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.job_title

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    employee_id = models.CharField(max_length=100, unique=True)
    manager = models.ForeignKey(Manager, on_delete=models.SET_NULL, null=True, blank=True)
    contact = models.CharField(max_length=15)
    status = models.CharField(max_length=10)
    job_type = models.ForeignKey(SalaryJobType, on_delete=models.SET_NULL, null=True, blank=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return self.name
class LeaveManager(models.Manager):
    def total_leave_days_for_employee(self, employee):
        today = timezone.localdate()
        start_of_month = today.replace(day=1)
        end_of_month = (start_of_month + timedelta(days=31)).replace(day=1) - timedelta(days=1)

        leave_days = self.filter(
            employee=employee, 
            status='Approved', 
            start_date__lte=end_of_month, 
            end_date__gte=start_of_month
        ).annotate(
            duration=models.ExpressionWrapper(
                models.F('end_date') - models.F('start_date') + timedelta(days=1),
                output_field=models.DurationField()
            )
        ).aggregate(total_days=models.Sum('duration'))

        return leave_days['total_days'].days if leave_days['total_days'] else 0

    def calculate_payroll(self, employee, total_leave_days):
        job_type = employee.job_type
        salary_job_type = SalaryJobType.objects.get(job_title=job_type)

        total_salary = salary_job_type.salary
        deduction_amount = total_leave_days * salary_job_type.deduction_money
        net_salary = total_salary - deduction_amount

        month_start = timezone.localdate().replace(day=1)
        month_end = (month_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)

        payroll, created = Payroll.objects.update_or_create(
            employee=employee,
            month__year=month_start.year,
            month__month=month_start.month,
            defaults={
                'total_salary': total_salary,
                'deduction_amount': deduction_amount,
                'net_salary': net_salary,
                'payment_date': timezone.localdate()
            }
        )
        return payroll

class Leave(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(max_length=20)
    

    
class Payroll(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    month = models.DateField()
    total_salary = models.DecimalField(max_digits=10, decimal_places=2)
    deduction_amount = models.DecimalField(max_digits=10, decimal_places=2)
    net_salary = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.employee.name} - {self.month}"