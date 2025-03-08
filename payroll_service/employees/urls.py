from django.contrib import admin
from django.urls import path
from employees import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('signup/employee/', views.signup_employee, name='signup_employee'),
    path('signup/manager/', views.signup_manager, name='signup_manager'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('employee_dashboard/', views.employee_dashboard, name='employee_dashboard'),
    path('manager_dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('apply_leave/', views.apply_leave, name='apply_leave'),
    path('show_leave_requests/', views.show_leave_requests, name='show_leave_requests'),
    path('manage_leave_request/<int:leave_id>/', views.manage_leave_request, name='manage_leave_request'),
    path('approve_employee/<int:employee_id>/', views.approve_employee, name='approve_employee'),
    path('reject_employee/<int:employee_id>/', views.reject_employee, name='reject_employee'),
    path('add_salary_job_type/', views.add_salary_job_type, name='add_salary_job_type'),
    path('calculate_payroll/', views.calculate_payroll, name='calculate_payroll'),
    path('show_payroll_details/', views.show_payroll_details, name='show_payroll_details'),

]
