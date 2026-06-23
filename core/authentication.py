from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import Attendance

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        result = super().authenticate(request)
        if result is None:
            return None
        
        user, token = result
        
        if user.role == 'staff':
            # Check if staff has an active attendance session
            has_active_session = Attendance.objects.filter(
                staff=user, 
                logout_time__isnull=True
            ).exists()
            
            if not has_active_session:
                raise AuthenticationFailed('Your session has been terminated by the owner.')
                
        return user, token
