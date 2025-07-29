from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from core.models import CustomUser


class ApiKeyAuthentication(BaseAuthentication):
    """Custom authentication for bot API keys"""
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        try:
            api_key = auth_header.split(' ')[1]
        except IndexError:
            raise AuthenticationFailed('Invalid authorization header format')
        
        try:
            user = CustomUser.objects.get(api_key=api_key, is_bot=True, is_active=True)
        except CustomUser.DoesNotExist:
            raise AuthenticationFailed('Invalid API key')
        
        return (user, None)
