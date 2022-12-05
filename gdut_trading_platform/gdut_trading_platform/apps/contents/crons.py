from collections import OrderedDict
from django.conf import settings
from django.template import loader
import os
import time

from .models import ContentCategory
from goods.models import GoodsChannel
from goods.utils import get_categories


def generate_static_index_html():
    """
    生成静态的主页html文件
    """
    print('%s: generate_static_index_html' % time.ctime())
    categories = get_categories()

    # 广告内容
    contents = {}
    content_categories = ContentCategory.objects.all()
    for cat in content_categories:
        contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')

    # 渲染模板
    context = {
        'categories': categories,  # 商品频道数据
        'contents': contents       # 广告数据
    }
    template = loader.get_template('index.html')    # get_template 加载模板界面
    html_text = template.render(context)            # 渲染模板
    # 评价路径 并 打开写入（如果不存在，就会新建并写入）
    # GENERATED_STATIC_HTML_FILES_DIR指向前端front_end_pc，生产环境下应指向nginx的静态文件目录下
    file_path = os.path.join(settings.GENERATED_STATIC_HTML_FILES_DIR, 'index.html')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_text)
