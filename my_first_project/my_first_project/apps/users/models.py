from django.db import models
from django.contrib.auth.models import AbstractUser
from itsdangerous import TimedJSONWebSignatureSerializer
from django.conf import settings
from my_first_project.utils.BaseModel import BaseModel

locker = TimedJSONWebSignatureSerializer(
    secret_key=settings.SECRET_KEY,
    expires_in=60 * 60 * 24
)


class User(AbstractUser):
    mobile = models.CharField(max_length=11, unique=True, verbose_name='手机号')
    email_active = models.BooleanField(default=False)
    default_address = models.ForeignKey('Address', null=True, blank=True, on_delete=models.SET_NULL,
                                        related_name='users')

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


class Address(BaseModel):
    user = models.ForeignKey('User', on_delete=models.CASCADE, verbose_name='用户')
    province = models.ForeignKey('areas.Areas', on_delete=models.PROTECT, related_name='province_addresses')
    city = models.ForeignKey('areas.Areas', on_delete=models.PROTECT, related_name='city_addresses')
    district = models.ForeignKey('areas.Areas', on_delete=models.PROTECT, related_name='district_addresses')
    title = models.CharField(max_length=20)
    receiver = models.CharField(max_length=20)
    place = models.CharField(max_length=50)
    mobile = models.CharField(max_length=11)
    tel = models.CharField(max_length=20, null=True, blank=True, default='')
    email = models.CharField(max_length=30, null=True, blank=True, default='')
    is_deleted = models.BooleanField(default=False)

    class Meta:
        db_table = 'tb_address'
        ordering = ['-update_time']
