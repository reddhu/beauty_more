from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse
from QQLoginTool.QQtool import OAuthQQ
from django.views import View
from .utils import check_access_token, generate_access_token
from .models import OAuthQQUser
from django.contrib.auth import login
from users.models import User
import json
import re
from django_redis import get_redis_connection
from django.contrib.auth import authenticate


class QQFirstView(View):
    def get(self, request):
        next_url = request.GET.get('next')
        oauth = OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            client_secret=settings.QQ_CLIENT_SECRET,
            redirect_uri=settings.QQ_REDIRECT_URI,
            state=next_url
        )
        login_url = oauth.get_qq_url()

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'login_url': login_url
        })


class QQSecondView(View):
    def get(self, request):
        code = request.GET.get('code')
        oauth = OAuthQQ(
            client_id=settings.QQ_CLIENT_ID,
            client_secret=settings.QQ_CLIENT_SECRET,
            redirect_uri=settings.QQ_REDIRECT_URI,
        )
        access_token = oauth.get_access_token(code)
        openid = oauth.get_open_id(access_token)
        try:
            qq_user = OAuthQQUser.objects.get(openid=openid)
        except Exception as e:
            access_token = generate_access_token(openid)
            return JsonResponse({
                'code': 400,
                'errmsg': '请绑定账户',
                'access_token': access_token
            })
        else:
            user = qq_user.user
            login(request, user)
            response = JsonResponse({
                'code': 0,
                'errmsg': 'ok'
            })
            response.set_cookie('username', user.username)
            return response

    def post(self, request):
        data_dict = json.loads(request.body)
        mobile = data_dict.get('mobile')
        password = data_dict.get('password')
        sms_code = data_dict.get('sms_code')
        access_token = data_dict.get('access_token')
        if not all([mobile, password, sms_code, access_token]):
            return JsonResponse({'code': 400, 'errmsg': '缺少必传参数'})
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '请输入正确的手机号码'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', password):
            return JsonResponse({'code': 400,
                                 'errmsg': '请输入8-20位的密码'})

        redis_conn = get_redis_connection('verify_code')
        try:
            sms_server = redis_conn.get(f'sms_{mobile}')
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': '验证码失效'})
        if sms_server.decode() != sms_code:
            return JsonResponse({'code': 400, 'errmsg': '验证码错误'})

        openid = check_access_token(access_token)
        try:
            qq_user = OAuthQQUser.objects.get(openid=openid)
            user = qq_user.user
        except Exception as e:
            try:
                user = User.objects.get(mobile=mobile)
                if not user.check_password(password):
                    return JsonResponse({'code': 400, 'errmsg': '密码错误'})
            except Exception as e:
                try:
                    user = User.objects.create_user(username=mobile, mobile=mobile, password=password)
                    qq_user = OAuthQQUser.objects.create(openid=openid, user=user)
                except Exception as e:
                    return JsonResponse({'code': 400, 'errmsg': '新建用户失败'})
            else:
                qq_user = OAuthQQUser.objects.create(openid=openid, user=user)

        login(request, user)
        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        response.set_cookie('username', user.username)
        return response
