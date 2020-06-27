from django.views import View
from .models import SKU, GoodsCategory
from django.core.paginator import Paginator
from django.http import JsonResponse
from .utils import get_bread_crumb
from haystack.views import SearchView


class ListView(View):
    def get(self, request, category_id):
        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        ordering = request.GET.get('ordering')
        goods = SKU.objects.filter(category_id=category_id).order_by(ordering)
        paging = Paginator(goods, page_size)
        return_list = []
        for good in paging.page(page):
            return_list.append({
                'id': good.id,
                'default_image_url': good.default_image_url,
                'name': good.name,
                'price': good.price
            })
        category = GoodsCategory.objects.get(pk=category_id)
        breadcrumb = get_bread_crumb(category)
        return JsonResponse({
            'code': 0, 'errmsg': 'ok', 'breadcrumb': breadcrumb, 'count': paging.num_pages, 'list': return_list
        })


class HotGoodsView(View):
    def get(self, request, category_id):
        goods = SKU.objects.filter(category_id=category_id)
        hot_skus = []
        for good in goods[:2]:
            hot_skus.append({
                'id': good.id, 'default_image_url': good.default_image_url, 'name': good.name, 'price': good.price
            })
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'hot_skus': hot_skus})


class MySearchView(SearchView):
    def create_response(self):
        data = self.get_context()
        data_list = []
        for good in data['page'].object_list:
            data_list.append({'id':good.object.id,'name':good.object.name,'price':good.object.price,
                              'default_image_url':good.object.default_image_url,'search_key':data.get('query'),
                              'page_size':data['paginator'].num_pages, 'count':data['page'].paginator.count
                              })
        return JsonResponse(data_list,safe=False)