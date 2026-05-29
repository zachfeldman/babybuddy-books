# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Book, BookReading


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "isbn")
    search_fields = ("title", "author", "isbn")


@admin.register(BookReading)
class BookReadingAdmin(admin.ModelAdmin):
    list_display = ("book", "child", "date_read")
    list_filter = ("child",)
    date_hierarchy = "date_read"
