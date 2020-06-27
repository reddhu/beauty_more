from django.views import View
from django.http import JsonResponse, HttpResponse
from .models import User, Address
import json
import re
from django_redis import get_redis_connection
from django.contrib.auth import login, authenticate, logout
import logging
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


class CreateAddressView(LoginRequiredMixin, View):
    def post(self, request):
        addresses = request.user.address_set.all()
        if len(addresses) >= 20:
            return JsonResponse({'code': 400, 'errmsg': '超过地址数量上限'})
        data = json.loads(request.body)
        receiver = data.get('receiver')
        province_id = data.get('province_id')
        city_id = data.get('city_id')
        district_id = data.get('district_id')
        place = data.get('place')
        mobile = data.get('mobile')
        tel = data.get('tel')
        email = data.get('email')
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400, 'errmsg': '参数有误'})
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})
        try:
            address = Address.objects.create(user=request.user, **data)
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': '数据库写入失败'})
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'address': address_dict})


#
class AddressView(LoginRequiredMixin, View):
    def get(self, request):
        data = Address.objects.filter(user=request.user, is_deleted=False)
        addresses = []
        default_address = request.user.default_address
        for address in data:
            if default_address == address:
                addresses.insert(0, {
                    'id': address.id,
                    'title': address.title,
                    'receiver': address.receiver,
                    'province': address.province.name,
                    'city': address.city.name,
                    'district': address.district.name,
                    'place': address.place,
                    'mobile': address.mobile,
                    'tel': address.tel,
                    'email': address.email
                })
            else:
                addresses.append({
                    'id': address.id,
                    'title': address.title,
                    'receiver': address.receiver,
                    'province': address.province.name,
                    'city': address.city.name,
                    'district': address.district.name,
                    'place': address.place,
                    'mobile': address.mobile,
                    'tel': address.tel,
                    'email': address.email
                })
        return JsonResponse({
            'code': 0, 'errmsg': 'ok', 'default_address_id': request.user.default_address_id, 'addresses': addresses
        })


class UpdateDestroyAddressView(LoginRequiredMixin, View):
    def put(self, request, address_id):
        """修改地址"""
        # 接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({'code': 400,
                                 'errmsg': '缺少必传参数'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})

        # 判断地址是否存在,并更新地址信息
        try:
            Address.objects.filter(id=address_id).update(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '更新地址失败'})

        # 构造响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 响应更新地址结果
        return JsonResponse({'code': 0,
                             'errmsg': '更新地址成功',
                             'address': address_dict})

    def delete(self, request, address_id):
        """删除地址"""
        try:
            # 查询要删除的地址
            address = Address.objects.get(id=address_id)

            # 将地址逻辑删除设置为True
            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '删除地址失败'})

        # 响应删除地址结果
        return JsonResponse({'code': 0,
                             'errmsg': '删除地址成功'})


class DefaultAddressView(LoginRequiredMixin, View):
    """设置默认地址"""

    def put(self, request, address_id):
        """设置默认地址"""
        try:
            # 接收参数,查询地址
            address = Address.objects.get(id=address_id)

            # 设置地址为默认地址
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '设置默认地址失败'})

        # 响应设置默认地址结果
        return JsonResponse({'code': 0,
                             'errmsg': '设置默认地址成功'})


class UpdateTitleAddressView(LoginRequiredMixin, View):
    """设置地址标题"""

    def put(self, request, address_id):
        """设置地址标题"""
        # 接收参数：地址标题
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        try:
            # 查询地址
            address = Address.objects.get(id=address_id)

            # 设置新的地址标题
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                                 'errmsg': '设置地址标题失败'})

        # 4.响应删除地址结果
        return JsonResponse({'code': 0,
                             'errmsg': '设置地址标题成功'})


class ChangePasswordView(LoginRequiredMixin, View):
    def put(self, request):
        data_dict = json.loads(request.body)
        old_password = data_dict.get('old_password')
        new_password = data_dict.get('new_password')
        new_password2 = data_dict.get('new_password2')
        if not all([old_password, new_password, new_password2]):
            return JsonResponse({'code': 400, 'errmsg': '参数不全'})
        if not request.user.check_password(old_password):
            return JsonResponse({'code': 400, 'errmsg': '旧密码错误'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return JsonResponse({'code': 400,
                                 'errmsg': '密码最少8位,最长20位'})
        if new_password != new_password2:
            return JsonResponse({'code': 400, 'errmsg': '两次输入密码不一样'})
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            return JsonResponse({'code': 400, 'errmsg': '设置新密码失败'})
        logout(request)
        return JsonResponse({'code': 0, 'errmsg': '密码修改成功'})
