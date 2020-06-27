from django.conf import settings
from goods.models import GoodsChannel, GoodsCategory, Goods
from .models import ContentCategory, Content
from django.template import loader
import os


def generate_static_index_html():
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

    context = {'categories': categories, 'contents': contents}
    template = loader.get_template('index.html')
    html_text = template.render(context=context)
    file_path = os.path.join(settings.GENERATE_STATIC_HTML, 'index.html')
    with open(file_path, 'w') as f:
        f.write(html_text)



