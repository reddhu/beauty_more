from django.shortcuts import render
from django.http import JsonResponse
from .models import Areas
from django.views import View
from django.core.cache import cache


class ProvinceListView(View):
    def get(self, request):
        provinces = Areas.objects.filter(parent=None)
        province_list = cache.get('province_list')
        if not province_list:
            province_list = []
            for temp in provinces:
                temp_dict = dict()
                temp_dict['id'] = temp.id
                temp_dict['name'] = temp.name
                province_list.append(temp_dict)
            cache.set('province_list', province_list, 3600)
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'province_list': province_list
        })


class SubAreaView(View):
    def get(self, request, pk):
        response = cache.get(f'response{pk}')
        if not response:
            parent = Areas.objects.get(pk=pk)
            sub_ares = parent.areas_set.all()
            response = {
                'code': 0, 'errmsg': 'ok', 'sub_data': {
                    'id': parent.id,
                    'name': parent.name,
                    'subs': []
                }
            }
            for temp in sub_ares:
                response['sub_data']['subs'].append({
                    'id': temp.id,
                    'name': temp.name
                })
            cache.set(f'response{pk}', response, 3600)
        return JsonResponse(response)
