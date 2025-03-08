from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from smtplib import SMTPException
from django.conf import settings
from .forms import UserForm, EmployeeForm, ManagerForm, LeaveForm,SalaryJobTypeForm
from .models import Employee, Manager, Leave , Payroll , SalaryJobType
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import models
from django.db.models import ExpressionWrapper, F, DurationField,Sum
from datetime import timedelta
def home(request):
    return render(request, 'home.html')

def signup_employee(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        employee_form = EmployeeForm(request.POST)
        if user_form.is_valid() and employee_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()
            employee = employee_form.save(commit=False)
            employee.user = user
            employee.save()
            employees_group, created = Group.objects.get_or_create(name='Employees')
            user.groups.add(employees_group)
            managers = Manager.objects.all()
            for manager in managers:
                send_mail(
                    'New Employee Signup',
                    f'Approve or reject the new employee/{employee.name}/: http://localhost:8000/approve_employee/{employee.id}/ or http://localhost:8000/reject_employee/{employee.id}/',
                    settings.EMAIL_HOST_USER,
                    [manager.user.email],
                    fail_silently=False
                )
            return render(request, 'success.html', {'message': 'Sign up successful. Awaiting approval.'})
    else:
        user_form = UserForm()
        employee_form = EmployeeForm()
    return render(request, 'signup_employee.html', {'user_form': user_form, 'employee_form': employee_form})

def signup_manager(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        manager_form = ManagerForm(request.POST)
        if user_form.is_valid() and manager_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()
            manager_group, created = Group.objects.get_or_create(name='Manager')
            user.groups.add(manager_group)
            manager = manager_form.save(commit=False)
            manager.user = user
            manager.save()
            login(request, user)
            return redirect('manager_dashboard')
    else:
        user_form = UserForm()
        manager_form = ManagerForm()
    return render(request, 'signup_manager.html', {'user_form': user_form, 'manager_form': manager_form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    if request.user.groups.filter(name='Manager').exists():
        return redirect('manager_dashboard')
    elif request.user.groups.filter(name='Employees').exists():
        # Check employee approval status before redirecting
        employee = Employee.objects.get(user=request.user)
        if not employee.is_approved:
            return render(request, 'error.html', {'message': 'Your account is not approved yet.'})
        return redirect('employee_dashboard')
    else:
        return render(request, 'error.html', {'message': 'You do not have the required permissions to access any dashboard.'})

@login_required
def employee_dashboard(request):
    try:
        employee = Employee.objects.get(user=request.user)
    except Employee.DoesNotExist:
        return render(request, 'error.html', {'message': 'No Employee matches the given query.'})

    if not employee.is_approved:
        return render(request, 'error.html', {'message': 'Your account is not approved yet.'})

    # Fetch leave requests
    leave_requests = Leave.objects.filter(employee=employee)
    
    # Calculate total approved leave days
    total_leave_days = Leave.objects.filter(
        employee=employee,
        status='Approved'
    ).aggregate(total_days= models.Sum(models.F('end_date') - models.F('start_date') + timedelta(days=1)))
    
    total_leave_days = total_leave_days['total_days'].days if total_leave_days['total_days'] else 0

    # Fetch payroll details
    payrolls = Payroll.objects.filter(employee=employee).order_by('-month')

    # Fetch job types (if needed in the template)
    job_types = SalaryJobType.objects.all()

    return render(request, 'employee_dashboard.html', {
        'leave_requests': leave_requests,
        'total_leave_days': total_leave_days,
        'payrolls': payrolls,
        'job_types': job_types
    })

@login_required
@user_passes_test(lambda u: u.groups.filter(name='Manager').exists())
def manager_dashboard(request):
    try:
        manager = Manager.objects.get(user=request.user)
    except Manager.DoesNotExist:
        return render(request, 'error.html', {'message': 'No Manager matches the given query.'})

    employees = Employee.objects.filter(manager=manager)
    return render(request, 'manager_dashboard.html', {'employees': employees})
@login_required
def apply_leave(request):
    if request.method == 'POST':
        leave_form = LeaveForm(request.POST)
        if leave_form.is_valid():
            leave = leave_form.save(commit=False)
            leave.employee = get_object_or_404(Employee, user=request.user)
            leave.status = 'Pending'
            leave.save()
            return redirect('employee_dashboard')
    else:
        leave_form = LeaveForm()
    return render(request, 'apply_leave.html', {'leave_form': leave_form})
@login_required
def show_leave_requests(request):
    manager = get_object_or_404(Manager, user=request.user)
    employees = Employee.objects.filter(manager=manager)
    leave_requests = Leave.objects.filter(employee__in=employees)
    return render(request, 'show_leave_requests.html', {'leave_requests': leave_requests})
@login_required
def manage_leave_request(request, leave_id):
    leave = get_object_or_404(Leave, id=leave_id)
    if request.method == 'POST':
        leave.status = request.POST['status']
        leave.save()
        try:
            send_mail(
                'Leave Request Update',
                f'Your leave request has been {leave.status.lower()}.',
                settings.EMAIL_HOST_USER,
                [leave.employee.user.email],
                fail_silently=False
            )
            messages.success(request, 'Leave request status updated and notification sent successfully.')
        except SMTPException as e:
            messages.error(request, f'Error sending email: {str(e)}. Please try again later.')
            # Optionally, log the error for further analysis
            # import logging
            # logger = logging.getLogger(__name__)
            # logger.error(f'SMTPException: {str(e)}')

        return redirect('show_leave_requests')
    
    return render(request, 'manage_leave_request.html', {'leave': leave})
@login_required
def approve_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    employee.is_approved = True
    employee.save()
    send_mail(
        'Employee Approved',
        'Your sign-up request has been approved.',
        settings.EMAIL_HOST_USER,
        [employee.user.email],
        fail_silently=False
    )
    return redirect('manager_dashboard')
@login_required
def reject_employee(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    employee.user.delete()
    employee.delete()
    send_mail(
        'Employee Rejected',
        'Your sign-up request has been rejected.',
        settings.EMAIL_HOST_USER,
        [employee.user.email],
        fail_silently=False
    )
    return redirect('manager_dashboard')
@login_required
def add_salary_job_type(request):
    if request.method == 'POST':
        form = SalaryJobTypeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Job type added successfully.')
            return redirect('add_salary_job_type')
    else:
        form = SalaryJobTypeForm()
    return render(request, 'add_salary_job_type.html', {'form': form})

@login_required
def calculate_payroll(request):
    leave_manager = LeaveManager()
    for employee in Employee.objects.all():
        total_leave_days = leave_manager.total_leave_days_for_employee(employee)
        leave_manager.calculate_payroll(employee, total_leave_days)
    messages.success(request, 'Payroll calculated successfully.')
    return redirect('manager_dashboard')

@login_required
def show_payroll_details(request):
    payrolls = Payroll.objects.filter(employee=request.user.employee)
    return render(request, 'show_payroll_details.html', {'payrolls': payrolls})