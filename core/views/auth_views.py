"""
Authentication views — Login (JWT + clock-in), Logout (+ clock-out), Token Refresh.
"""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.utils import timezone
from django.utils import timezone
from ..models import Attendance, User, LoginRequest
from ..serializers import LoginSerializer, UserSerializer, LoginRequestSerializer

class PendingLoginsView(APIView):
    """GET /api/auth/pending-logins/"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'owner':
            return Response([])
        pending_qs = LoginRequest.objects.filter(status='pending').order_by('created_at')
        return Response(LoginRequestSerializer(pending_qs, many=True).data)

class LoginView(APIView):
    """
    POST /api/auth/login/
    Authenticates user, issues JWT pair, and creates an Attendance record (clock-in).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        if user.role == 'owner':
            # Owner logs in immediately
            refresh = RefreshToken.for_user(user)
            today = timezone.localdate()
            # Auto clock-out any stuck open sessions
            open_sessions = Attendance.objects.filter(staff=user, logout_time__isnull=True)
            for session in open_sessions:
                session.clock_out()
                
            # Create a fresh attendance record for this login
            Attendance.objects.create(
                staff=user,
                date=today,
                login_time=timezone.now(),
            )
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
            }, status=status.HTTP_200_OK)
        else:
            # Staff needs approval
            login_req = LoginRequest.objects.create(
                staff=user,
                status='pending'
            )
            return Response({
                'status': 'pending',
                'request_id': login_req.id,
            }, status=status.HTTP_202_ACCEPTED)

class LoginStatusView(APIView):
    """
    GET /api/auth/login-status/<id>/
    Staff polls this endpoint. If approved, issues JWT.
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            req = LoginRequest.objects.get(pk=pk)
        except LoginRequest.DoesNotExist:
            return Response({'status': 'invalid'}, status=status.HTTP_404_NOT_FOUND)

        if req.status == 'approved':
            # Issue token and clock in
            user = req.staff
            refresh = RefreshToken.for_user(user)
            today = timezone.localdate()
            # Auto clock-out any stuck open sessions
            open_sessions = Attendance.objects.filter(staff=user, logout_time__isnull=True)
            for session in open_sessions:
                session.clock_out()
                
            # Create a fresh attendance record for this login
            Attendance.objects.create(
                staff=user,
                date=today,
                login_time=timezone.now(),
            )
            return Response({
                'status': 'approved',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data,
            }, status=status.HTTP_200_OK)
        
        return Response({'status': req.status}, status=status.HTTP_200_OK)

class ApproveLoginView(APIView):
    """POST /api/auth/login-approve/<id>/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            req = LoginRequest.objects.get(pk=pk, status='pending')
            req.status = 'approved'
            req.save()
            return Response({'status': 'approved'})
        except LoginRequest.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

class RejectLoginView(APIView):
    """POST /api/auth/login-reject/<id>/"""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if request.user.role != 'owner':
            return Response(status=status.HTTP_403_FORBIDDEN)
        try:
            req = LoginRequest.objects.get(pk=pk, status='pending')
            req.status = 'rejected'
            req.save()
            return Response({'status': 'rejected'})
        except LoginRequest.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)



class LogoutView(APIView):
    """
    POST /api/auth/logout/
    Blacklists the refresh token and clocks out the user (attendance).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass  # Token may already be blacklisted or invalid

        # Auto clock-out: update any open attendance
        open_sessions = Attendance.objects.filter(
            staff=request.user,
            logout_time__isnull=True,
        )
        for session in open_sessions:
            session.clock_out()

        return Response({'detail': 'Logged out successfully.'}, status=status.HTTP_200_OK)


class CustomTokenRefreshView(TokenRefreshView):
    """POST /api/auth/refresh/ — Standard JWT refresh."""
    pass


class MeView(APIView):
    """GET /api/auth/me/ — Returns current user info."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteProfilePhotoView(APIView):
    """DELETE /api/auth/me/photo/"""
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        if user.profile_photo:
            user.profile_photo.delete(save=False)
            user.profile_photo = None
            user.save()
        return Response(UserSerializer(user).data)
