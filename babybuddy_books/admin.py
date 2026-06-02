# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Book, BookReading


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "isbn")
    search_fields = ("title", "author", "isbn")


@admin.register(BookReading)
class BookReadingAdmin(admin.ModelAdmin):
    list_display = ("book", "child", "start", "duration")
    list_filter = ("child",)
    date_hierarchy = "start"
