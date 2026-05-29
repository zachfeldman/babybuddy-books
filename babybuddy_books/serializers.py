# -*- coding: utf-8 -*-
from rest_framework import serializers

from .models import Book, BookReading


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "isbn",
            "cover_url",
            "openlibrary_id",
            "created_at",
        ]
        read_only_fields = ["created_at"]


class BookReadingSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)
    child_name = serializers.CharField(source="child.__str__", read_only=True)

    class Meta:
        model = BookReading
        fields = [
            "id",
            "child",
            "child_name",
            "book",
            "book_title",
            "date_read",
            "notes",
            "created_at",
        ]
        read_only_fields = ["created_at"]
