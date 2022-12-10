from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """自定义查询集分页类"""
    page_size = 2
    page_size_query_param = 'page_size'   # page_size字段名
    max_page_size = 20
