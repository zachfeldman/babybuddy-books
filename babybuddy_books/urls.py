# -*- coding: utf-8 -*-
from django.urls import path

from . import views

app_name = "books"

urlpatterns = [
    # Books
    path("books/", views.BookList.as_view(), name="book-list"),
    path("books/add/", views.BookAdd.as_view(), name="book-add"),
    path("books/<int:pk>/edit/", views.BookUpdate.as_view(), name="book-update"),
    path("books/<int:pk>/delete/", views.BookDelete.as_view(), name="book-delete"),
    # Readings
    path("books/readings/", views.BookReadingList.as_view(), name="reading-list"),
    path("books/readings/add/", views.BookReadingAdd.as_view(), name="reading-add"),
    path(
        "books/readings/<int:pk>/edit/",
        views.BookReadingUpdate.as_view(),
        name="reading-update",
    ),
    path(
        "books/readings/<int:pk>/delete/",
        views.BookReadingDelete.as_view(),
        name="reading-delete",
    ),
    # JSON endpoints (consumed by books.js)
    path("books/search/", views.book_local_search, name="book-search"),
    path("books/quick-add/", views.book_quick_add, name="book-quick-add"),
    path("books/title-search/", views.book_title_search, name="title-search"),
    path("books/isbn-lookup/", views.book_isbn_lookup, name="isbn-lookup"),
]
