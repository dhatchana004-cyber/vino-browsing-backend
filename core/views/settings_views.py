"""
Settings API views — PAN card permissions & password change.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ..models import StaffPermission, OpeningBalance, SystemSettings
from ..serializers import (
    StaffPermissionSerializer,
    PasswordChangeSerializer,
    OpeningBalanceSerializer,
)
from ..permissions import IsOwner


class StaffPermissionListView(APIView):
    """
    GET  /api/settings/permissions/ — List PAN card permissions.
    POST /api/settings/permissions/ — Add permission for a staff member.
    """
    permission_classes = [IsOwner]

    def get(self, request):
        perms = StaffPermission.objects.select_related('staff').all()
        return Response(StaffPermissionSerializer(perms, many=True).data)

    def post(self, request):
        serializer = StaffPermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class StaffPermissionDeleteView(APIView):
    """DELETE /api/settings/permissions/{id}/ — Remove a permission."""
    permission_classes = [IsOwner]

    def delete(self, request, pk):
        try:
            perm = StaffPermission.objects.get(pk=pk)
            perm.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except StaffPermission.DoesNotExist:
            return Response({'detail': 'Not found.'}, status=status.HTTP_404_NOT_FOUND)


class ChangePasswordView(APIView):
    """POST /api/settings/change-password/ — Change own password."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'detail': 'Password changed successfully.'})


class OpeningBalanceView(APIView):
    """
    GET  /api/settings/opening-balance/?date= — Get opening balance for date.
    POST /api/settings/opening-balance/ — Set/update opening balance.
    """
    permission_classes = [IsOwner]

    def get(self, request):
        from django.utils import timezone
        date = request.query_params.get('date', timezone.localdate().isoformat())
        balance = OpeningBalance.objects.filter(date=date).first()
        if balance:
            return Response(OpeningBalanceSerializer(balance).data)
        return Response({'amount': 0, 'date': date})

    def post(self, request):
        from django.utils import timezone
        date_val = request.data.get('date', timezone.localdate().isoformat())
        amount = request.data.get('amount', 0)

        balance, created = OpeningBalance.objects.update_or_create(
            date=date_val,
            defaults={'amount': amount, 'set_by': request.user},
        )
        return Response(OpeningBalanceSerializer(balance).data)


class ReportPasswordView(APIView):
    """
    POST /api/settings/reports-password/ — Set/Update the global reports password
    """
    permission_classes = [IsOwner]

    def post(self, request):
        try:
            current_password = request.data.get('current_password', '')
            new_password = request.data.get('new_password', '')
            settings = SystemSettings.get_settings()
            
            if settings.reports_password and settings.reports_password != current_password:
                return Response({'detail': 'Incorrect current password.'}, status=status.HTTP_400_BAD_REQUEST)
                
            settings.reports_password = new_password
            settings.save()
            return Response({'detail': 'Reports password updated successfully.'})
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyReportPasswordView(APIView):
    """
    POST /api/settings/verify-reports-password/ — Verify the reports password
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        password = request.data.get('password', '')
        settings = SystemSettings.get_settings()
        
        if not settings.reports_password or settings.reports_password == password:
            return Response({'success': True})
            
        return Response({'success': False, 'detail': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)

