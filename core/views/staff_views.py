"""
Staff Management API views — Owner-only CRUD for staff users.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.utils import timezone
from ..models import User, Attendance, ServiceEntry
from ..serializers import UserSerializer, StaffCreateSerializer, ResetPasswordSerializer
from ..permissions import IsOwner


class StaffListCreateView(APIView):
    """
    GET  /api/staff/ — List all staff with status.
    POST /api/staff/ — Create new staff user.
    """
    permission_classes = [IsOwner]

    def get(self, request):
        staff = User.objects.filter(role='staff', is_deleted=False)
        today = timezone.localdate()

        # Auto-close orphaned attendance sessions from previous days
        orphaned = Attendance.objects.filter(
            logout_time__isnull=True
        ).exclude(date=today)
        for session in orphaned:
            session.clock_out()

        # TEMPORARY FIX: Automatically rename any old deleted users on the live database
        deleted_users = User.objects.filter(role='deleted_staff')
        import uuid
        for u in deleted_users:
            if '_del_' not in u.username:
                u.username = f"{u.username}_del_{str(uuid.uuid4())[:6]}"
                u.save()

        staff_data = []
        for s in staff:
            # Only check today's open sessions for online status
            is_online = Attendance.objects.filter(
                staff=s, date=today, logout_time__isnull=True
            ).exists()
            today_entries = ServiceEntry.objects.filter(staff=s, date=today).count()

            data = UserSerializer(s).data
            data['is_online'] = is_online
            data['today_entries'] = today_entries
            staff_data.append(data)

        return Response(staff_data)

    def post(self, request):
        serializer = StaffCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class StaffDetailView(APIView):
    """
    PATCH /api/staff/{id}/ — Update staff details.
    DELETE /api/staff/{id}/ — Soft-delete staff (hides from list, preserves data).
    """
    permission_classes = [IsOwner]

    def patch(self, request, pk):
        try:
            staff = User.objects.get(pk=pk, role='staff', is_deleted=False)
        except User.DoesNotExist:
            return Response({'detail': 'Staff not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        # Only allow updating specific fields
        if 'first_name' in request.data:
            staff.first_name = request.data['first_name']
        if 'username' in request.data:
            staff.username = request.data['username']
        if 'is_active' in request.data:
            staff.is_active = request.data['is_active']
        
        staff.save()
        return Response(UserSerializer(staff).data)

    def delete(self, request, pk):
        try:
            staff = User.objects.get(pk=pk, role='staff', is_deleted=False)
        except User.DoesNotExist:
            return Response({'detail': 'Staff not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Soft delete: prevent login and hide from Staff Management, but keep data
        staff.is_active = False
        staff.is_deleted = True
        staff.deleted_at = timezone.now()
        staff.role = 'deleted_staff'
        import uuid
        staff.username = f"{staff.username}_del_{str(uuid.uuid4())[:6]}"
        staff.save()

        # Force logout just in case
        tokens = OutstandingToken.objects.filter(user=staff)
        for token in tokens:
            try:
                BlacklistedToken.objects.get_or_create(token=token)
            except Exception:
                pass

        return Response({'detail': f'{staff.username} has been deleted.'})


class StaffResetPasswordView(APIView):
    """POST /api/staff/{id}/reset-password/ — Reset staff password."""
    permission_classes = [IsOwner]

    def post(self, request, pk):
        try:
            staff = User.objects.get(pk=pk, role='staff')
        except User.DoesNotExist:
            return Response({'detail': 'Staff not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        staff.set_password(serializer.validated_data['new_password'])
        staff.save()
        return Response({'detail': f'Password reset for {staff.username}.'})


class StaffForceLogoutView(APIView):
    """POST /api/staff/{id}/logout/ — Force logout staff (blacklist tokens + clock-out)."""
    permission_classes = [IsOwner]

    def post(self, request, pk):
        try:
            staff = User.objects.get(pk=pk, role='staff')
        except User.DoesNotExist:
            return Response({'detail': 'Staff not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Blacklist all outstanding tokens for this staff
        tokens = OutstandingToken.objects.filter(user=staff)
        for token in tokens:
            try:
                BlacklistedToken.objects.get_or_create(token=token)
            except Exception:
                pass

        # Clock out any open sessions
        attendances = Attendance.objects.filter(
            staff=staff, logout_time__isnull=True
        )
        for att in attendances:
            att.clock_out()

        return Response({'detail': f'{staff.username} has been logged out.'})
