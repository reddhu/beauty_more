import os
from django.conf import settings
from django.template import loader
from contents.models import ContentCategory
from goods.models import GoodsChannel, GoodsCategory, SKU, SpecificationOption, GoodsSpecification, SKUSpecification
from copy import deepcopy


def get_bread_crumb(category):
    breadcrumb = {
        'cat1': None,
        'cat2': None,
        'cat3': None
    }
    if not category.parent:
        breadcrumb['cat1'] = category.name

    elif not category.parent.parent:
        breadcrumb['cat2'] = category.name
        breadcrumb['cat1'] = category.parent.name
    else:
        breadcrumb['cat3'] = category.name
        breadcrumb['cat2'] = category.parent.name
        breadcrumb['cat1'] = category.parent.parent.name
    return breadcrumb


def get_goods_and_spec(sku_id):
    sku = SKU.objects.get(pk=sku_id)
    goods = sku.goods
    skus = SKU.objects.filter(goods=goods)
    empty_dict = dict()
    for sku_good in skus:
        empty_list = []
        sku_combinations = SKUSpecification.objects.filter(sku=sku_good).order_by('spec_id')
        for temp in sku_combinations:
            empty_list.append(temp.option_id)
        empty_dict[tuple(empty_list)] = sku_good.id

    sku_list = []
    cur_sku_spec_options = SKUSpecification.objects.filter(sku=sku).order_by('spec_id')
    for temp in cur_sku_spec_options:
        sku_list.append(temp.option_id)

    spec_set = GoodsSpecification.objects.filter(goods=goods).order_by('id')

    for index, spec in enumerate(spec_set):
        options = SpecificationOption.objects.filter(spec=spec)
        for option in options:
            temp_list = deepcopy(sku_list)
            temp_list[index] = option.id
            option.sku_id = empty_dict.get(tuple(temp_list))
        spec.spec_options = options
    return goods, spec_set, sku


def generate_static_sku_detail_html(sku_id):
    goods, specs, sku = get_goods_and_spec(sku_id)
    categories = get_categories()
    context = {
        'categories': categories,
        'goods': goods,
        'specs': specs,
        'sku': sku
    }
    template = loader.get_template('detail.html')
    html_text = template.render(context)
    file_path = os.path.join(settings.GENERATE_STATIC_HTML, 'goods/' + str(sku_id) + '.html')
    with open(file_path, 'w') as f:
        f.write(html_text)


def get_categories():
    categories = {}
    channels = GoodsChannel.objects.all().order_by('group_id', 'sequence')
    for channel in channels:
        if channel.group_id not in categories:
            categories[channel.group_id] = {'channels': [],
                                            'sub_cats': []}
        cat1 = channel.category
        categories[channel.group_id]['channels'].append({
            'id': cat1.id, 'name': cat1.name, 'url': channel.url
        })
        sub_cats_1 = GoodsCategory.objects.filter(parent=cat1)
        for sub_cart_1 in sub_cats_1:
            sub_carts2 = []
            sub_carts_2 = GoodsCategory.objects.filter(parent=sub_cart_1)
            for sub_cart_2 in sub_carts_2:
                sub_carts2.append({
                    'id': sub_cart_2.id, 'name': sub_cart_2.name
                })
            categories[channel.group_id]['sub_cats'].append({
                'id': sub_cart_1.id, 'name': sub_cart_1.name, 'sub_cats': sub_carts2
            })
    contents = {}
    content_categories = ContentCategory.objects.all()
    for content_category in content_categories:
        contents[content_category.key] = content_category.content_set.all()
    return categories
