from django.shortcuts import render
from django.views import View
from my_first_project.utils.StringGenerator import randomString, randomNumber
from captcha.image import ImageCaptcha
from django_redis import get_redis_connection
from django.http import HttpResponse, JsonResponse
import logging

logger = logging.getLogger('django')
from my_first_project.utils.yuntongxun.ccp_sms import CCP


# Create your views here.


class ImageCodeView(View):
    def get(self, request, uuid):
        text = randomString()
        image = ImageCaptcha()
        image = image.generate(text)
        redis_conn = get_redis_connection('verify_code')
        try:
            redis_conn.setex(f'img_{uuid}', 300, text)
        except Exception as e:
            logger.info(e)
            return JsonResponse({
                'code': 400,
                'errmsg': '出错啦'
            })
        return HttpResponse(image, content_type='image/jpg')


class SMSCodeView(View):
    def get(self, request, mobile):
        img_code_cli = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')
        if not all([uuid, img_code_cli]):
            return JsonResponse({
                'code': 400,
                'errmsg': '参数获取不全'
            })
        redis_conn = get_redis_connection('verify_code')
        img_code_server = redis_conn.get(f'img_{uuid}')
        if not img_code_server:
            return JsonResponse({
                'code': 400,
                'errmsg': '验证码过期'
            })
        try:
            redis_conn.delete(f'img_{uuid}')
        except Exception as e:
            logger.info(e)
        if img_code_cli.lower() != img_code_server.decode().lower():
            return JsonResponse({
                'code': 400,
                'errmsg': '验证码错误'
            })
        if redis_conn.ttl(f'sms_{mobile}')>240:
            redis_conn.delete(f'sms_{mobile}')
            return JsonResponse({
                'code': 400,
                'errmsg': '请勿频繁发送'
            })
        sms_code = randomNumber()
        redis_conn.set(f'sms_{mobile}', 300, sms_code)
        CCP().send_template_sms('15334200702', (sms_code, 5), 1)
        return JsonResponse({
            'code': 0,
            'errmsg': '短信发送成功'
        })