"""
Django Admin configuration for VINO models.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Customer, Service, ServiceEntry,
    Attendance, Expense, StaffPermission, OpeningBalance,
)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'first_name', 'last_name', 'role', 'is_active']
    list_filter = ['role', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('VINO', {'fields': ('role',)}),
    )


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'created_at']
    search_fields = ['name', 'phone']


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']


@admin.register(ServiceEntry)
class ServiceEntryAdmin(admin.ModelAdmin):
    list_display = ['customer_name', 'service', 'staff', 'amount', 'charge',
                    'profit', 'status', 'date']
    list_filter = ['status', 'service', 'staff', 'date']
    search_fields = ['customer_name', 'phone', 'srn_number']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['staff', 'date', 'login_time', 'logout_time', 'working_hours']
    list_filter = ['staff', 'date']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'date', 'created_by']
    list_filter = ['date']


@admin.register(StaffPermission)
class StaffPermissionAdmin(admin.ModelAdmin):
    list_display = ['staff', 'permission']
    list_filter = ['permission']


@admin.register(OpeningBalance)
class OpeningBalanceAdmin(admin.ModelAdmin):
    list_display = ['date', 'amount', 'set_by']
