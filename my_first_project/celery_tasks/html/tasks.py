from goods.utils import get_goods_and_spec, get_categories
from django.conf import settings
from django.template import loader
import os
from celery_tasks.main import celery_app
@celery_app.task(name='generate_static_sku_detail_html')
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
