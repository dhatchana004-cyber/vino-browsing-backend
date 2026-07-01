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
