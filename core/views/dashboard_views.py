"""
Dashboard API view — Today's live stats for the owner dashboard.
"""
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Sum, Count, Q
from ..models import ServiceEntry, Expense, Attendance, User, OpeningBalance, LoginRequest
from ..serializers import ServiceEntryListSerializer, ExpenseSerializer, LoginRequestSerializer


class DashboardView(APIView):
    """
    GET /api/dashboard/
    Returns today's aggregated stats for the owner dashboard.
    Staff gets their own stats only.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        today = timezone.localdate()
        user = request.user

        # Base queryset — owner sees all, staff sees own
        entries_qs = ServiceEntry.objects.filter(date=today)
        if user.role == 'staff':
            entries_qs = entries_qs.filter(staff=user)

        # Aggregations
        totals = entries_qs.aggregate(
            total_amount=Sum('amount'),
            total_charge=Sum('charge'),
            total_profit=Sum('profit'),
            total_entries=Count('id'),
        )

        total_amount = totals['total_amount'] or Decimal('0')
        total_charge = totals['total_charge'] or Decimal('0')
        total_profit = totals['total_profit'] or Decimal('0')
        total_entries = totals['total_entries'] or 0

        # Today's expenses
        expenses_qs = Expense.objects.filter(date=today).order_by('-created_at')
        total_expenses = expenses_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Opening balance
        opening = OpeningBalance.objects.filter(date=today).first()
        opening_balance = opening.amount if opening else Decimal('0')

        # Final profit = opening_balance + profit - expenses
        final_profit = opening_balance + total_profit - total_expenses

        # Unique customers today
        total_customers = entries_qs.values('phone').distinct().count()

        # Staff status and pending logins (owner only)
        staff_status = []
        pending_logins = []
        if user.role == 'owner':
            pending_qs = LoginRequest.objects.filter(status='pending').order_by('created_at')
            pending_logins = LoginRequestSerializer(pending_qs, many=True).data

            staff_users = User.objects.filter(role='staff', is_active=True)
            for s in staff_users:
                attendance = Attendance.objects.filter(staff=s, logout_time__isnull=True).first()
                is_working = attendance is not None
                # Count today's entries for this staff
                staff_entries = ServiceEntry.objects.filter(staff=s, date=today)
                staff_totals = staff_entries.aggregate(
                    count=Count('id'),
                    amount=Sum('amount'),
                )
                staff_status.append({
                    'id': s.id,
                    'name': s.get_full_name() or s.username,
                    'profile_photo': request.build_absolute_uri(s.profile_photo.url) if s.profile_photo else None,
                    'is_working': is_working,
                    'login_time': attendance.login_time.isoformat() if attendance else None,
                    'entries_count': staff_totals['count'] or 0,
                    'total_amount': float(staff_totals['amount'] or 0),
                })

        # Recent entries (latest 10)
        recent = entries_qs.select_related('service', 'staff').order_by('-created_at')[:10]

        return Response({
            'total_amount': float(total_amount),
            'total_charge': float(total_charge),
            'total_profit': float(total_profit),
            'total_expenses': float(total_expenses),
            'expenses': ExpenseSerializer(expenses_qs, many=True).data,
            'opening_balance': float(opening_balance),
            'final_profit': float(final_profit),
            'total_entries': total_entries,
            'total_customers': total_customers,
            'staff_status': staff_status,
            'pending_logins': pending_logins,
            'recent_entries': ServiceEntryListSerializer(recent, many=True).data,
        })
