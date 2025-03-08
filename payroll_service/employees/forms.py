# forms.py

from django import forms
from django.contrib.auth.models import User
from .models import Employee, Manager, Leave,SalaryJobType

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'password', 'email']

class ManagerForm(forms.ModelForm):
    class Meta:
        model = Manager
        fields = ['name', 'manager_id', 'contact']

class EmployeeForm(forms.ModelForm):
    job_type = forms.ModelChoiceField(queryset=SalaryJobType.objects.all(), empty_label="Select Job Type", required=True)
    class Meta:
        model = Employee
        fields = ['name', 'employee_id', 'contact', 'job_type', 'manager']

class LeaveForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = ['start_date', 'end_date', 'reason']
        
class SalaryJobTypeForm(forms.ModelForm):
    class Meta:
        model = SalaryJobType
        fields = ['job_title', 'salary', 'deduction_money']