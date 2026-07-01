"""
URL routing for all VINO API endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.auth_views import (
    LoginView, LogoutView, CustomTokenRefreshView, MeView,
    LoginStatusView, ApproveLoginView, RejectLoginView, PendingLoginsView,
    DeleteProfilePhotoView
)
from .views.entry_views import ServiceEntryViewSet
from .views.customer_views import CustomerViewSet
from .views.service_views import ServiceViewSet
from .views.dashboard_views import DashboardView
from .views.report_views import (
    DailyReportView, MonthlyReportView, YearlyReportView, StaffDailyReportView
)
from .views.attendance_views import AttendanceViewSet, TodayAttendanceView, AttendanceSummaryView
from .views.staff_views import (
    StaffListCreateView, StaffDetailView,
    StaffResetPasswordView, StaffForceLogoutView
)
from .views.expense_views import ExpenseViewSet
from .views.download_views import (
    DownloadAllView, DownloadDailyView, DownloadMonthlyView,
    DownloadYearlyView, DownloadStaffView, DownloadCustomersView,
    DownloadExpensesView
)
from .views.settings_views import (
    StaffPermissionListView, StaffPermissionDeleteView,
    ChangePasswordView, OpeningBalanceView,
    ReportPasswordView, VerifyReportPasswordView,
    SystemSettingsView,
)
from .views.publicsite_views import (
    SiteSettingsView, WhyChooseUsListCreateView, WhyChooseUsDetailView,
    PublicServiceListCreateView, PublicServiceDetailView,
    JobUpdateListCreateView, JobUpdateDetailView, PublicSiteDataView,
    EducationApplicationListCreateView, EducationApplicationDetailView
)

# DRF router for ViewSets
router = DefaultRouter()
router.register(r'entries', ServiceEntryViewSet, basename='entries')
router.register(r'customers', CustomerViewSet, basename='customers')
router.register(r'services', ServiceViewSet, basename='services')
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'expenses', ExpenseViewSet, basename='expenses')

urlpatterns = [
    # Auth
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/login-status/<int:pk>/', LoginStatusView.as_view(), name='auth-login-status'),
    path('auth/login-approve/<int:pk>/', ApproveLoginView.as_view(), name='auth-login-approve'),
    path('auth/login-reject/<int:pk>/', RejectLoginView.as_view(), name='auth-login-reject'),
    path('auth/pending-logins/', PendingLoginsView.as_view(), name='auth-pending-logins'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/refresh/', CustomTokenRefreshView.as_view(), name='auth-refresh'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
    path('auth/me/photo/', DeleteProfilePhotoView.as_view(), name='auth-me-photo-delete'),

    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    # Reports
    path('reports/daily/', DailyReportView.as_view(), name='reports-daily'),
    path('reports/monthly/', MonthlyReportView.as_view(), name='reports-monthly'),
    path('reports/yearly/', YearlyReportView.as_view(), name='reports-yearly'),
    path('reports/staff-daily/', StaffDailyReportView.as_view(), name='reports-staff-daily'),

    # Attendance today
    path('attendance/today/', TodayAttendanceView.as_view(), name='attendance-today'),
    path('attendance/summary/', AttendanceSummaryView.as_view(), name='attendance-summary'),

    # Staff management (owner only)
    path('staff/', StaffListCreateView.as_view(), name='staff-list-create'),
    path('staff/<int:pk>/', StaffDetailView.as_view(), name='staff-detail'),
    path('staff/<int:pk>/reset-password/', StaffResetPasswordView.as_view(), name='staff-reset-password'),
    path('staff/<int:pk>/logout/', StaffForceLogoutView.as_view(), name='staff-force-logout'),

    # Downloads
    path('download/all/', DownloadAllView.as_view(), name='download-all'),
    path('download/daily/', DownloadDailyView.as_view(), name='download-daily'),
    path('download/monthly/', DownloadMonthlyView.as_view(), name='download-monthly'),
    path('download/yearly/', DownloadYearlyView.as_view(), name='download-yearly'),
    path('download/staff/', DownloadStaffView.as_view(), name='download-staff'),
    path('download/customers/', DownloadCustomersView.as_view(), name='download-customers'),
    path('download/expenses/', DownloadExpensesView.as_view(), name='download-expenses'),

    # Settings
    path('settings/', SystemSettingsView.as_view(), name='system-settings'),
    path('settings/permissions/', StaffPermissionListView.as_view(), name='settings-permissions'),
    path('settings/permissions/<int:pk>/', StaffPermissionDeleteView.as_view(), name='settings-permission-delete'),
    path('settings/change-password/', ChangePasswordView.as_view(), name='settings-change-password'),
    path('settings/opening-balance/', OpeningBalanceView.as_view(), name='settings-opening-balance'),
    path('settings/reports-password/', ReportPasswordView.as_view(), name='settings-reports-password'),
    path('settings/verify-reports-password/', VerifyReportPasswordView.as_view(), name='settings-verify-reports-password'),

    # Router URLs (entries, customers, services, attendance, expenses)
    path('', include(router.urls)),

    # Public Site Management
    path('public-site/settings/', SiteSettingsView.as_view(), name='public-site-settings'),
    path('public-site/why-choose-us/', WhyChooseUsListCreateView.as_view(), name='public-site-why-choose-us'),
    path('public-site/why-choose-us/<int:pk>/', WhyChooseUsDetailView.as_view(), name='public-site-why-choose-us-detail'),
    path('public-site/services/', PublicServiceListCreateView.as_view(), name='public-site-services'),
    path('public-site/services/<int:pk>/', PublicServiceDetailView.as_view(), name='public-site-service-detail'),
    path('public-site/jobs/', JobUpdateListCreateView.as_view(), name='public-site-jobs'),
    path('public-site/jobs/<int:pk>/', JobUpdateDetailView.as_view(), name='public-site-job-detail'),
    path('public-site/education/', EducationApplicationListCreateView.as_view(), name='public-site-education'),
    path('public-site/education/<int:pk>/', EducationApplicationDetailView.as_view(), name='public-site-education-detail'),
    path('public-site/data/', PublicSiteDataView.as_view(), name='public-site-data'),
]
