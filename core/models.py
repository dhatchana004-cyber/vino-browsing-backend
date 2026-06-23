"""
VINO Browsing Management System — Database Models

All 7 core models for the browsing center management system.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone


class User(AbstractUser):
    """Custom user with role-based access (owner or staff)."""

    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('staff', 'Staff'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='staff')
    is_active = models.BooleanField(default=True)
    profile_photo = models.ImageField(upload_to='profiles/', null=True, blank=True)

    class Meta:
        ordering = ['username']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

    @property
    def is_owner(self):
        return self.role == 'owner'

    @property
    def is_staff_role(self):
        return self.role == 'staff'


class Customer(models.Model):
    """Customer record — identified primarily by phone number."""

    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15, blank=True, db_index=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.phone})" if self.phone else self.name


class Service(models.Model):
    """Service type catalog (Aadhaar, Passport, Ration Card, etc.)."""

    name = models.CharField(max_length=200, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ServiceEntry(models.Model):
    """
    Core transaction record — one service performed for one customer.
    Profit is auto-calculated as amount - charge.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('informed', 'Informed'),
        ('dispatched', 'Dispatched'),
        ('successful', 'Successful'),
        ('rejected', 'Rejected'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entries',
    )
    customer_name = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='entries',
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        related_name='entries',
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    charge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    srn_number = models.CharField(max_length=100, blank=True, db_index=True)
    remarks = models.TextField(blank=True)
    document = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'pdf'])],
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
    )
    date = models.DateField(default=timezone.localdate, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Service Entries'

    def __str__(self):
        name = self.customer_name or (self.customer.name if self.customer else 'Unknown')
        return f"{name} — {self.service.name} (₹{self.amount})"

    def save(self, *args, **kwargs):
        """Auto-calculate profit before saving."""
        self.profit = self.amount - self.charge
        super().save(*args, **kwargs)


class Attendance(models.Model):
    """
    Auto-tracked attendance — created on login, updated on logout.
    Working hours computed from login/logout times.
    """

    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='attendance_records',
    )
    login_time = models.DateTimeField()
    logout_time = models.DateTimeField(null=True, blank=True)
    working_hours = models.DurationField(null=True, blank=True)
    date = models.DateField(db_index=True)

    class Meta:
        ordering = ['-date', '-login_time']

    def __str__(self):
        return f"{self.staff.username} — {self.date}"

    def clock_out(self):
        """Set logout time and calculate working hours."""
        from django.utils import timezone
        self.logout_time = timezone.now()
        self.working_hours = self.logout_time - self.login_time
        self.save()


class Expense(models.Model):
    """Daily expense tracking for the browsing center."""

    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(db_index=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='expenses',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.title} — ₹{self.amount} ({self.date})"


class StaffPermission(models.Model):
    """Granular permission flags per staff member."""

    PERMISSION_CHOICES = [
        ('edit_records', 'Edit Records'),
    ]

    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='staff_permissions',
    )
    permission = models.CharField(max_length=50, choices=PERMISSION_CHOICES)

    class Meta:
        unique_together = ('staff', 'permission')

    def __str__(self):
        return f"{self.staff.username} — {self.permission}"


class OpeningBalance(models.Model):
    """Daily opening balance set by the owner each morning."""

    date = models.DateField(unique=True, db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    set_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='opening_balances',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Opening Balance {self.date}: ₹{self.amount}"


class LoginRequest(models.Model):
    """Pending login requests for staff."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('timeout', 'Timeout'),
    ]

    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_requests',
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"LoginRequest {self.staff.username} - {self.status}"


class SystemSettings(models.Model):
    """Global system settings."""
    reports_password = models.CharField(max_length=128, blank=True)

    class Meta:
        verbose_name_plural = 'System Settings'
        
    def __str__(self):
        return "System Settings"

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj


# ===========================================================================
# Public Site Models
# ===========================================================================

class SiteSettings(models.Model):
    """Singleton model for public site configuration."""

    # Top Bar
    address = models.TextField(blank=True, default='')
    hours = models.CharField(max_length=200, blank=True, default='')
    holiday = models.CharField(max_length=200, blank=True, default='')

    # Header
    shop_name = models.CharField(max_length=200, blank=True, default='VINO Browsing Center')
    community_link = models.URLField(max_length=500, blank=True, default='')
    whatsapp = models.CharField(max_length=20, blank=True, default='')

    # Hero Section
    hero_title = models.CharField(max_length=300, blank=True, default='')
    hero_photo = models.ImageField(upload_to='site/', null=True, blank=True)
    hero_service_tags = models.TextField(blank=True, default='',
        help_text='Comma-separated service tags for hero section')

    # Footer / Contact
    email = models.EmailField(blank=True, default='')
    map_url = models.URLField(max_length=500, blank=True, default='')
    instagram_link = models.URLField(max_length=500, blank=True, default='')
    youtube_link = models.URLField(max_length=500, blank=True, default='')

    class Meta:
        verbose_name_plural = 'Site Settings'

    def __str__(self):
        return "Site Settings"

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj


class WhyChooseUsPoint(models.Model):
    """Individual point in the 'Why Choose Us' section."""

    text = models.CharField(max_length=300)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.text


class PublicService(models.Model):
    """Service card displayed on the public site."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')
    icon = models.CharField(max_length=50, blank=True, default='',
        help_text='Emoji or icon name')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return self.title


class JobUpdate(models.Model):
    """Job vacancy/update displayed on the public site."""

    title = models.CharField(max_length=200)
    exam_name = models.CharField(max_length=200, blank=True, default='')
    image = models.ImageField(upload_to='jobs/', null=True, blank=True)
    post_count = models.CharField(max_length=100, blank=True, default='')
    qualification = models.CharField(max_length=200, blank=True, default='')
    last_date = models.DateField(null=True, blank=True)
    exam_date = models.DateField(null=True, blank=True)
    
    description = models.TextField(blank=True, default='')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.start_date} to {self.end_date})"


class EducationApplication(models.Model):
    """Education application updates displayed on the public site."""

    exam_name = models.CharField(max_length=200)
    last_date = models.DateField(null=True, blank=True)
    exam_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_date', '-created_at']

    def __str__(self):
        return self.exam_name

