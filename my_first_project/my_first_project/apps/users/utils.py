from django.contrib.auth.backends import ModelBackend
from .models import User


class UsernameMobileAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as e:
            try:
                user = User.objects.get(mobile=username)
            except User.DoesNotExist as e:
                return None
        if user.check_password(password):
            return user
