"""
DRF Serializers for the VINO Browsing Management System.
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import (
    User, Customer, Service, ServiceEntry,
    Attendance, Expense, StaffPermission, OpeningBalance, LoginRequest,
    SiteSettings, WhyChooseUsPoint, PublicService, JobUpdate, EducationApplication,
    SystemSettings,
)


# ---------------------------------------------------------------------------
# Auth Serializers
# ---------------------------------------------------------------------------
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(required=False)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user is None:
            raise serializers.ValidationError('Invalid username or password.')
        if not user.is_active:
            raise serializers.ValidationError('This account has been deactivated.')
        if 'role' in data and data['role'] and user.role != data['role']:
            raise serializers.ValidationError(f"Invalid account type. Please use the {user.role.title()} login tab.")
        data['user'] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'full_name',
                  'role', 'is_active', 'date_joined', 'permissions', 'profile_photo']
        read_only_fields = ['id', 'date_joined']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_permissions(self, obj):
        return list(obj.staff_permissions.values_list('permission', flat=True))




class StaffCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=4)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data['role'] = 'staff'
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=4)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=4)


# ---------------------------------------------------------------------------
# Customer Serializers
# ---------------------------------------------------------------------------
class CustomerSerializer(serializers.ModelSerializer):
    visit_count = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    last_visit = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'address', 'notes',
                  'visit_count', 'total_paid', 'last_visit', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_visit_count(self, obj):
        return obj.entries.count()

    def get_total_paid(self, obj):
        total = obj.entries.aggregate(total=models.Sum('amount'))['total']
        return float(total) if total else 0

    def get_last_visit(self, obj):
        last = obj.entries.order_by('-created_at').first()
        return last.date.isoformat() if last else None


class CustomerDetailSerializer(CustomerSerializer):
    entries = serializers.SerializerMethodField()

    class Meta(CustomerSerializer.Meta):
        fields = CustomerSerializer.Meta.fields + ['entries']

    def get_entries(self, obj):
        entries = obj.entries.select_related('service', 'staff').order_by('-created_at')[:50]
        return ServiceEntryListSerializer(entries, many=True).data


# ---------------------------------------------------------------------------
# Service Serializers
# ---------------------------------------------------------------------------
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


# ---------------------------------------------------------------------------
# Service Entry Serializers
# ---------------------------------------------------------------------------
class ServiceEntrySerializer(serializers.ModelSerializer):
    """Full serializer for create/update operations."""

    class Meta:
        model = ServiceEntry
        fields = [
            'id', 'customer', 'customer_name', 'phone', 'staff',
            'service', 'amount', 'charge', 'profit', 'srn_number',
            'remarks', 'document', 'status', 'date', 'created_at',
        ]
        read_only_fields = ['id', 'profit', 'date', 'created_at']

    def validate_document(self, value):
        if value and value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError('File size must not exceed 5 MB.')
        return value

    def create(self, validated_data):
        # Auto-calculate profit
        validated_data['profit'] = validated_data.get('amount', 0) - validated_data.get('charge', 0)

        # Auto-create/link customer if phone provided
        phone = validated_data.get('phone', '')
        customer_name = validated_data.get('customer_name', '')
        if phone and not validated_data.get('customer'):
            customer, _ = Customer.objects.get_or_create(
                phone=phone,
                defaults={'name': customer_name or 'Unknown'},
            )
            validated_data['customer'] = customer

        return super().create(validated_data)


class ServiceEntryListSerializer(serializers.ModelSerializer):
    """Read-only serializer with nested service/staff names."""

    service_name = serializers.CharField(source='service.name', read_only=True)
    staff_name = serializers.SerializerMethodField()

    class Meta:
        model = ServiceEntry
        fields = [
            'id', 'customer_name', 'phone', 'service', 'service_name',
            'staff', 'staff_name', 'amount', 'charge', 'profit',
            'srn_number', 'document', 'status', 'date', 'created_at',
        ]

    def get_staff_name(self, obj):
        return obj.staff.get_full_name() or obj.staff.username


class StatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=ServiceEntry.STATUS_CHOICES)


# ---------------------------------------------------------------------------
# Attendance Serializers
# ---------------------------------------------------------------------------
class AttendanceSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()
    working_hours_display = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = ['id', 'staff', 'staff_name', 'login_time', 'logout_time',
                  'working_hours', 'working_hours_display', 'date']

    def get_staff_name(self, obj):
        return obj.staff.get_full_name() or obj.staff.username

    def get_working_hours_display(self, obj):
        if obj.working_hours:
            total_seconds = int(obj.working_hours.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
        if obj.login_time and not obj.logout_time:
            from django.utils import timezone
            delta = timezone.now() - obj.login_time
            total_seconds = int(delta.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m (active)"
        return '-'


# ---------------------------------------------------------------------------
# Expense Serializers
# ---------------------------------------------------------------------------
class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id', 'title', 'amount', 'date', 'created_by', 'created_at']
        read_only_fields = ['id', 'created_by', 'created_at']


# ---------------------------------------------------------------------------
# Staff Permission Serializers
# ---------------------------------------------------------------------------
class StaffPermissionSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()

    class Meta:
        model = StaffPermission
        fields = ['id', 'staff', 'staff_name', 'permission']

    def get_staff_name(self, obj):
        return obj.staff.get_full_name() or obj.staff.username


# ---------------------------------------------------------------------------
# Opening Balance Serializer
# ---------------------------------------------------------------------------
class OpeningBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = OpeningBalance
        fields = ['id', 'date', 'amount', 'set_by', 'created_at']
        read_only_fields = ['id', 'set_by', 'created_at']


# ---------------------------------------------------------------------------
# System Settings Serializer
# ---------------------------------------------------------------------------
class SystemSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSettings
        fields = ['reports_password', 'attendance_late_time', 'attendance_working_days']
        extra_kwargs = {
            'reports_password': {'write_only': True},
        }


# ---------------------------------------------------------------------------
# Login Request Serializer
# ---------------------------------------------------------------------------
class LoginRequestSerializer(serializers.ModelSerializer):
    staff_name = serializers.SerializerMethodField()

    class Meta:
        model = LoginRequest
        fields = ['id', 'staff', 'staff_name', 'status', 'created_at']

    def get_staff_name(self, obj):
        return obj.staff.get_full_name() or obj.staff.username


# ---------------------------------------------------------------------------
# Dashboard Serializer
# ---------------------------------------------------------------------------
class DashboardSerializer(serializers.Serializer):
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_charge = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_profit = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=10, decimal_places=2)
    opening_balance = serializers.DecimalField(max_digits=10, decimal_places=2)
    final_profit = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_entries = serializers.IntegerField()
    total_customers = serializers.IntegerField()
    staff_status = serializers.ListField()
    recent_entries = ServiceEntryListSerializer(many=True)


# Need to import models for aggregate
from django.db import models as db_models

# Patch CustomerSerializer to use correct models reference
CustomerSerializer.get_total_paid = lambda self, obj: float(
    obj.entries.aggregate(total=db_models.Sum('amount'))['total'] or 0
)


# ---------------------------------------------------------------------------
# Public Site Serializers
# ---------------------------------------------------------------------------
class SiteSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteSettings
        fields = [
            'id', 'shop_name', 'address', 'hours', 'holiday',
            'community_link', 'whatsapp', 'email', 'map_url', 'instagram_link', 'youtube_link',
            'hero_title', 'hero_photo', 'hero_service_tags',
        ]


class WhyChooseUsPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhyChooseUsPoint
        fields = ['id', 'text', 'order']


class PublicServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PublicService
        fields = ['id', 'title', 'description', 'icon', 'order', 'is_active']


class JobUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobUpdate
        fields = [
            'id', 'title', 'exam_name', 'image', 'post_count', 
            'qualification', 'last_date', 'exam_date', 
            'description', 'start_date', 'end_date', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class EducationApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationApplication
        fields = [
            'id', 'title', 'exam_name', 'image', 'post_count', 
            'qualification', 'last_date', 'exam_date', 
            'description', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

