"""
Report API views — Daily, Monthly, Yearly summaries.
"""
from decimal import Decimal
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import date, timedelta
from ..models import ServiceEntry, Expense, OpeningBalance
from ..serializers import ServiceEntryListSerializer


class DailyReportView(APIView):
    """GET /api/reports/daily/?date=YYYY-MM-DD"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date and end_date:
            try:
                start_date = date.fromisoformat(start_date)
                end_date = date.fromisoformat(end_date)
            except ValueError:
                start_date = end_date = timezone.localdate()
        else:
            start_date = end_date = timezone.localdate()

        entries_qs = ServiceEntry.objects.filter(date__range=[start_date, end_date])
        if request.user.role == 'staff':
            entries_qs = entries_qs.filter(staff=request.user)

        totals = entries_qs.aggregate(
            total_amount=Sum('amount'),
            total_charge=Sum('charge'),
            total_profit=Sum('profit'),
            total_entries=Count('id'),
        )

        # Expenses
        expenses_total = Expense.objects.filter(date__range=[start_date, end_date]).aggregate(
            total=Sum('amount'))['total'] or Decimal('0')

        # Opening balance (from the first day of the range)
        opening = OpeningBalance.objects.filter(date=start_date).first()
        opening_balance = opening.amount if opening else Decimal('0')

        profit = totals['total_profit'] or Decimal('0')
        final_profit = opening_balance + profit - expenses_total

        # Unique customers
        total_customers = entries_qs.values('phone').exclude(phone='').distinct().count()

        # Service breakdown
        service_breakdown = entries_qs.values('service__name').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            total_profit=Sum('profit'),
        ).order_by('-total_amount')

        # Entries list
        entries = entries_qs.select_related('service', 'staff').order_by('-created_at')

        return Response({
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_amount': float(totals['total_amount'] or 0),
            'total_charge': float(totals['total_charge'] or 0),
            'total_profit': float(profit),
            'total_expenses': float(expenses_total),
            'opening_balance': float(opening_balance),
            'final_profit': float(final_profit),
            'total_entries': totals['total_entries'] or 0,
            'total_customers': total_customers,
            'service_breakdown': list(service_breakdown),
            'entries': ServiceEntryListSerializer(entries, many=True).data,
        })


class MonthlyReportView(APIView):
    """GET /api/reports/monthly/?month=MM&year=YYYY"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.localdate()
        month = int(request.query_params.get('month', now.month))
        year = int(request.query_params.get('year', now.year))

        entries_qs = ServiceEntry.objects.filter(date__year=year, date__month=month)
        if request.user.role == 'staff':
            entries_qs = entries_qs.filter(staff=request.user)

        totals = entries_qs.aggregate(
            total_amount=Sum('amount'),
            total_charge=Sum('charge'),
            total_profit=Sum('profit'),
            total_entries=Count('id'),
        )

        expenses_total = Expense.objects.filter(
            date__year=year, date__month=month
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Daily breakdown within month
        daily_breakdown = entries_qs.values('date').annotate(
            entries_count=Count('id'),
            total_amount=Sum('amount'),
            total_charge=Sum('charge'),
            total_profit=Sum('profit'),
        ).order_by('date')

        # Service breakdown
        service_breakdown = entries_qs.values('service__name').annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            total_profit=Sum('profit'),
        ).order_by('-total_amount')

        # Staff breakdown (owner only)
        staff_breakdown = []
        if request.user.role == 'owner':
            staff_breakdown = list(
                entries_qs.values('staff__username', 'staff__first_name').annotate(
                    count=Count('id'),
                    total_amount=Sum('amount'),
                    total_charge=Sum('charge'),
                    total_profit=Sum('profit'),
                ).order_by('-total_profit')
            )

        return Response({
            'month': month,
            'year': year,
            'total_amount': float(totals['total_amount'] or 0),
            'total_charge': float(totals['total_charge'] or 0),
            'total_profit': float(profit),
            'total_expenses': float(expenses_total),
            'opening_balance': float(opening_total),
            'final_profit': float(final_profit),
            'total_entries': totals['total_entries'] or 0,
            'total_customers': total_customers,
            'daily_breakdown': list(daily_breakdown),
            'service_breakdown': list(service_breakdown),
            'staff_breakdown': staff_breakdown,
        })


class YearlyReportView(APIView):
    """GET /api/reports/yearly/?year=YYYY"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year = int(request.query_params.get('year', timezone.localdate().year))

        entries_qs = ServiceEntry.objects.filter(date__year=year)
        if request.user.role == 'staff':
            entries_qs = entries_qs.filter(staff=request.user)

        totals = entries_qs.aggregate(
            total_amount=Sum('amount'),
            total_charge=Sum('charge'),
            total_profit=Sum('profit'),
            total_entries=Count('id'),
        )

        expenses_total = Expense.objects.filter(
            date__year=year
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')

        # Monthly breakdown
        monthly_breakdown = entries_qs.values('date__month').annotate(
            entries_count=Count('id'),
            total_amount=Sum('amount'),
            total_charge=Sum('charge'),
            total_profit=Sum('profit'),
        ).order_by('date__month')

        return Response({
            'year': year,
            'total_amount': float(totals['total_amount'] or 0),
            'total_charge': float(totals['total_charge'] or 0),
            'total_profit': float(profit),
            'total_expenses': float(expenses_total),
            'opening_balance': float(opening_total),
            'final_profit': float(final_profit),
            'total_entries': totals['total_entries'] or 0,
            'total_customers': total_customers,
            'monthly_breakdown': list(monthly_breakdown),
        })


class StaffDailyReportView(APIView):
    """GET /api/reports/staff-daily/?date=YYYY-MM-DD — Staff-wise daily breakdown."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if start_date and end_date:
            try:
                start_date = date.fromisoformat(start_date)
                end_date = date.fromisoformat(end_date)
            except ValueError:
                start_date = end_date = timezone.localdate()
        else:
            start_date = end_date = timezone.localdate()

        entries_qs = ServiceEntry.objects.filter(date__range=[start_date, end_date])

        staff_breakdown = entries_qs.values(
            'staff__id', 'staff__username', 'staff__first_name'
        ).annotate(
            count=Count('id'),
            total_amount=Sum('amount'),
            total_charge=Sum('charge'),
            total_profit=Sum('profit'),
        ).order_by('-total_profit')

        return Response({
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'staff_breakdown': list(staff_breakdown),
        })
