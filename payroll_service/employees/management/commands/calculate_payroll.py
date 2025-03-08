from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from employees.models import Employee, Leave,Payroll
from django.db.models import ExpressionWrapper, F, DurationField, Sum

class Command(BaseCommand):
    help = 'Calculate payroll for the previous month'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        first_day_of_current_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_current_month - timedelta(days=1)
        first_day_of_last_month = last_day_of_last_month.replace(day=1)
        month = last_day_of_last_month.strftime('%B %Y')

        employees = Employee.objects.all()
        for employee in employees:
            total_leave_days = Leave.objects.filter(
                employee=employee,
                status='Approved',
                start_date__lte=last_day_of_last_month,
                end_date__gte=first_day_of_last_month
            ).annotate(
                duration=ExpressionWrapper(
                    F('end_date') - F('start_date') + timedelta(days=1),
                    output_field=DurationField()
                )
            ).aggregate(total_days=Sum('duration'))

            leave_days = total_leave_days['total_days'].days if total_leave_days['total_days'] else 0

            job_type = employee.job_type
            if job_type:
                total_salary = job_type.salary
                deduction_amount = leave_days * job_type.deduction_money
                net_salary = total_salary - deduction_amount

                Payroll.objects.create(
                    employee=employee,
                    month=first_day_of_last_month,
                    total_salary=total_salary,
                    deduction_amount=deduction_amount,
                    net_salary=net_salary,
                    payment_status='Pending'
                )