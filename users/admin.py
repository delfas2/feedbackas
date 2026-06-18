from django.contrib import admin
from .models import Company, Department, ContractSettings, EmployeeCountLog

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email_domain', 'created_at', 'is_active')
    search_fields = ('name', 'email_domain')
    list_filter = ('is_active', 'created_at')

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'parent', 'manager')
    search_fields = ('name', 'company__name', 'manager__username', 'manager__first_name', 'manager__last_name')
    list_filter = ('company',)

@admin.register(ContractSettings)
class ContractSettingsAdmin(admin.ModelAdmin):
    list_display = ('company', 'price_per_employee', 'minimum_fee', 'contract_start', 'contract_end')
    search_fields = ('company__name',)
    list_filter = ('company',)

@admin.register(EmployeeCountLog)
class EmployeeCountLogAdmin(admin.ModelAdmin):
    list_display = ('company', 'active_count', 'recorded_at')
    search_fields = ('company__name',)
    list_filter = ('company', 'recorded_at')
