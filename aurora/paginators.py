"""Модуль пагинации для приложения aurora."""

from rest_framework import pagination


class CoursePagination(pagination.PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 10


class LessonPagination(pagination.PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 20
