from django.views import View
from django.http import JsonResponse, HttpResponse
from .models import User
import json
import re
from django_redis import get_redis_connection
from django.contrib.auth import login, authenticate, logout
import logging
from django.core.mail import send_mail
from celery_tasks.email.tasks import send_email
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin

logger = logging.getLogger('django')


class UsernameCountView(View):
    def get(self, request, username):
        count = User.objects.filter(username=username).count()
        return JsonResponse({
            'code': 0,
            'count': count,
            'errmsg': 'ok'
        })


class MobileCountView(View):
    def get(self, request, phone_num):
        count = User.objects.filter(mobile=phone_num).count()
        return JsonResponse({
            'code': 0,
            'count': count,
            'errmsg': 'ok'
        })


class RegisterView(View):
    def post(self, request):
        data_dict = json.loads(request.body)  # 身体
        password = data_dict.get('password')
        password2 = data_dict.get('password2')
        mobile = data_dict.get('mobile')
        username = data_dict.get('username')
        sms_code = data_dict.get('sms_code')
        allow = data_dict.get('allow')

        if not all([username, password, password2, mobile, sms_code]):
            return JsonResponse({
                'code': 400,
                'errmsg': '参数不全'
            })
        if not re.match(r'^[a-zA-Z0-9]{5,20}$', username):  # 匹配
            return JsonResponse({
                'code': 400,
                'errmsg': '账号格式有误'
            })
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return JsonResponse({
                'code': 400,
                'errmsg': '密码格式有误'
            })
        if not isinstance(allow, bool):
            return JsonResponse({
                'code': 400,
                'errmsg': 'allow格式有误'
            })
        if not allow:
            return JsonResponse({
                'code': 400,
                'errmsg': '请同意用户协议'
            })
        if password != password2:
            return JsonResponse({
                'code': 400,
                'errmsg': '两次密码输入不一样'
            })
        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get(f'sms_{mobile}')
        if not sms_code_server:
            return JsonResponse({
                'code': 400,
                'errmsg': '验证码过期'
            })
        if sms_code != sms_code_server.decode():
            return JsonResponse({
                'code': 400,
                'errmsg': '手机验证码错误'
            })
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except Exception as e:
            logger.error(e)
            return JsonResponse({
                'code': 400,
                'errmsg': '账号写入失败'
            })
        login(request, user)

        response = JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })
        response.set_cookie('username', username, max_age=3600 * 24 * 14)
        return response


class LoginView(View):
    def post(self, request):
        data_dict = json.loads(request.body)
        username = data_dict.get('username')
        password = data_dict.get('password')
        remembered = data_dict.get('remembered')
        if not re.match(r'^[a-zA-Z0-9]{5,20}$', username):
            return JsonResponse({
                'code': 400,
                'errmsg': '账号格式有误'
            })
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return JsonResponse({
                'code': 400,
                'errmsg': '密码格式有误'
            })
        user = authenticate(request, username=username, password=password)
        if not user:
            return JsonResponse({
                'code': 400,
                'errmsg': '账号密码不匹配'
            })
        login(request, user)
        response = JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })
        if remembered:
            request.session.set_expiry(None)
        else:
            request.session.set_expiry(0)
        response.set_cookie('username', user.username, max_age=3600 * 24 * 14)
        return response


class LogoutView(View):
    def delete(self, request):  # flush  remove clear strip erase
        logout(request)
        response = JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })
        response.delete_cookie('username')
        return response


class UserInfoView(LoginRequiredMixin, View):
    def get(self, request):
        print('用户中心函数')
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'info_data': {
                'username': request.user.username,
                'mobile': request.user.mobile,
                'email': request.user.email,
                'email_active': request.user.email_active,
            }
        })


class EmailView(View):
    def put(self, request):
        data = json.loads(request.body)
        to_email = data.get('email')
        if not to_email:
            return JsonResponse({'code': 400,
                                 'errmsg': '缺少email参数'})
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', to_email):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数email有误'})
        try:
            request.user.email = to_email
            request.user.save()
        except Exception as e:
            return JsonResponse({
                'code': 400, 'errmsg': '数据写入失败'
            })
        token = request.user.generate_token()
        verify_url = settings.EMAIL_VERIFY_URL + token
        send_email.delay(to_email, verify_url)

        return JsonResponse({'code': 200, 'errmsg': 'ok'})


class VerifyEmailView(View):
    def put(self, request):
        token = request.GET.get('token')
        user = User.check_token(token)
        if user:
            try:
                user.email_active = True
                user.save()
            except Exception as e:
                return JsonResponse({'code': 400, 'errmsg': '数据写入失败'})
        else:
            return None

        return HttpResponse({'code': 0, 'errmsg': 'ok'})
