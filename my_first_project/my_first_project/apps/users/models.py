from django.db import models
from django.contrib.auth.models import AbstractUser
from itsdangerous import TimedJSONWebSignatureSerializer
from django.conf import settings

locker = TimedJSONWebSignatureSerializer(
    secret_key=settings.SECRET_KEY,
    expires_in=60 * 60 * 24
)


class User(AbstractUser):
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    email_active = models.BooleanField(default=False)

    class Meta:
        db_table = 'tb_users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    def generate_token(self, ):
        result = locker.dumps({
            'user_id': self.id,
            'email': self.email
        })
        return result.decode()

    @staticmethod
    def check_token(token):
        try:
            result = locker.loads(token)
        except Exception as e:
            return None
        user_id = result.get('user_id')
        user = User.objects.get(id=user_id)
        return user
