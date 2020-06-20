from django.shortcuts import render
from django.views import View
from django.http import JsonResponse, HttpResponse
from .models import User
import captcha


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


