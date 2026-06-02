# -*- coding: utf-8 -*-
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Book, BookReading
from .serializers import BookReadingSerializer, BookSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["isbn"]
    search_fields = ["title", "author", "isbn"]


class BookReadingViewSet(viewsets.ModelViewSet):
    queryset = BookReading.objects.all().select_related("book", "child")
    serializer_class = BookReadingSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["child", "book", "start", "end"]


def register_api(router):
    """Called by Baby Buddy's api/urls.py to register our viewsets."""
    router.register(r"books", BookViewSet)
    router.register(r"book-readings", BookReadingViewSet, basename="book-readings")
