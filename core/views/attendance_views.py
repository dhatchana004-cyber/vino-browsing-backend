"""
Attendance API views — List and today's live attendance.
"""
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from django.utils import timezone
from ..models import Attendance, User
from ..serializers import AttendanceSerializer
from ..permissions import IsOwner


class AttendanceFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='date', lookup_expr='lte')
    month = filters.NumberFilter(field_name='date', lookup_expr='month')
    year = filters.NumberFilter(field_name='date', lookup_expr='year')

    class Meta:
        model = Attendance
        fields = ['staff', 'date']


class AttendanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/attendance/ — List attendance records with filters.
    Owner sees all; staff sees own.
    """
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AttendanceFilter

    def get_queryset(self):
        # Auto-close orphaned attendance sessions from previous days
        today = timezone.localdate()
        orphaned = Attendance.objects.filter(
            logout_time__isnull=True
        ).exclude(date=today)
        for session in orphaned:
            session.clock_out()

        qs = Attendance.objects.select_related('staff').filter(staff__role='staff')
        if self.request.user.role == 'staff':
            qs = qs.filter(staff=self.request.user)
        return qs


class TodayAttendanceView(APIView):
    """
    GET /api/attendance/today/
    Returns today's attendance for all staff with live working hours.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        records = Attendance.objects.filter(date=today, staff__role='staff').select_related('staff')

        if request.user.role == 'staff':
            records = records.filter(staff=request.user)

        data = AttendanceSerializer(records, many=True).data

        # Add entry counts for each staff
        from ..models import ServiceEntry
        from django.db.models import Sum, Count
        for record in data:
            staff_entries = ServiceEntry.objects.filter(
                staff_id=record['staff'], date=today
            ).aggregate(
                count=Count('id'),
                total_amount=Sum('amount'),
            )
            record['entries_count'] = staff_entries['count'] or 0
            record['total_amount'] = float(staff_entries['total_amount'] or 0)

        return Response(data)


class AttendanceSummaryView(APIView):
    """
    GET /api/attendance/summary/?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD

    Returns present/late/leave counts per staff member over the given date range.
    The calculation uses attendance_late_time and attendance_working_days
    from SystemSettings.
    """
    permission_classes = [IsAuthenticated, IsOwner]

    def get(self, request):
        from datetime import date, timedelta, datetime as dt
        from ..models import SystemSettings

        date_from_str = request.query_params.get('date_from')
        date_to_str = request.query_params.get('date_to')

        if not date_from_str or not date_to_str:
            return Response(
                {'error': 'Both date_from and date_to query parameters are required.'},
                status=400,
            )

        try:
            date_from = date.fromisoformat(date_from_str)
            date_to = date.fromisoformat(date_to_str)
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD.'},
                status=400,
            )

        # Load settings
        settings = SystemSettings.get_settings()
        late_time = settings.attendance_late_time
        working_days = [
            int(d.strip())
            for d in settings.attendance_working_days.split(',')
            if d.strip().isdigit()
        ]
        # Convert our convention (0=Sun,1=Mon,...6=Sat)
        # Python isoweekday(): Mon=1,...Sun=7
        # We map: 0->7(Sun), 1->1(Mon), 2->2(Tue),...6->6(Sat)
        working_isoweekdays = set()
        for d in working_days:
            working_isoweekdays.add(7 if d == 0 else d)

        today = timezone.localdate()

        # Fetch all staff users
        staff_users = User.objects.filter(role='staff', is_active=True)

        # Fetch all attendance records in range
        records = Attendance.objects.filter(
            date__gte=date_from,
            date__lte=date_to,
            staff__role='staff',
        ).select_related('staff')

        # Group records by staff_id -> date -> list of login_times
        from collections import defaultdict
        staff_records = defaultdict(lambda: defaultdict(list))
        for rec in records:
            login_local = timezone.localtime(rec.login_time)
            staff_records[rec.staff_id][rec.date].append(login_local.time())

        # Build summary for each staff
        summary = {}
        for staff in staff_users:
            present = 0
            late = 0
            leaves = 0
            staff_dates = staff_records.get(staff.id, {})

            current_date = date_from
            while current_date <= date_to:
                day_iso = current_date.isoweekday()
                login_times = staff_dates.get(current_date, [])

                if login_times:
                    # Staff has at least one login on this date → Present
                    present += 1
                    # Check if the earliest login is strictly after late_time
                    earliest = min(login_times)
                    if earliest > late_time:
                        late += 1
                else:
                    # No login on this date
                    is_working_day = day_iso in working_isoweekdays
                    has_passed = current_date < today
                    
                    # Do not count leave for days before the staff member was created/hired
                    joined_date = timezone.localtime(staff.date_joined).date()
                    is_after_join = current_date >= joined_date

                    if is_working_day and has_passed and is_after_join:
                        leaves += 1

                current_date += timedelta(days=1)

            staff_name = staff.get_full_name() or staff.username
            summary[str(staff.id)] = {
                'staff_name': staff_name,
                'present': present,
                'late': late,
                'leaves': leaves,
            }

        return Response({'summary': summary})
