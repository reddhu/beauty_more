from django.test import TestCase
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'my_first_project.settings.dev')
import django

django.setup()

from django.conf import settings
from goods.models import GoodsChannel, GoodsCategory, Goods
from contents.models import ContentCategory, Content
from django.template import loader
import os


def generate_static_index_html():
    categories = {}
    cat1s = GoodsChannel.objects.all().order_by('group_id', 'sequence')
    for cat1 in cat1s:
        cat1.name = cat1.category.name
        if cat1.group_id not in categories:
            categories[cat1.group_id] = {
                'channels': [],
                'sub_cats': []
            }
        categories[cat1.group_id]['channels'].append(cat1)
        cat2s = GoodsCategory.objects.filter(parent_id=cat1.category_id)
        for cat2 in cat2s:
            cat2.sub_cats = []
            cat3s = GoodsCategory.objects.filter(parent=cat2)
            for cat3 in cat3s:
                cat2.sub_cats.append(cat3)
            categories[cat1.group_id]['sub_cats'].append(cat2)

    contents = {}
    ads = ContentCategory.objects.all()
    for ad in ads:
        contents[ad.key] = ad.content_set.all()

    context = {
        'categories': categories,
        'contents': contents
    }
    template = loader.get_template('index.html')
    html_file = template.render(context)
    file_path = os.path.join(settings.GENERATE_STATIC_HTML, 'index.html')
    with open(file_path, 'w') as f:
        f.write(html_file)
    return categories


if __name__ == '__main__':
    print(generate_static_index_html())
