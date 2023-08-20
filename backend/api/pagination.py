from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """
    Класс пагинации для ограничения количества элементов на странице.

    Параметры:
    - page_size: Количество элементов на странице по умолчанию.
    - page_size_query_param: Параметр запроса,
    позволяющий клиенту задавать количество
    элементов на странице.
    """
    page_size = 6
    page_size_query_param = 'limit'
