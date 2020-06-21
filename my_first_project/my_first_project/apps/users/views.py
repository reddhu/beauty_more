from django.views import View
from django.http import JsonResponse, HttpResponse
from .models import User
import json
import re
from django_redis import get_redis_connection
from django.contrib.auth import login, authenticate
import logging

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
        data_dict = json.loads(request.body)
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
        response.set_cookie('username', username)
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
        response.set_cookie('username', username)
        return response


