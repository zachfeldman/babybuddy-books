# -*- coding: utf-8 -*-
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Book(models.Model):
    """A book that can be read to a child."""

    title = models.CharField(max_length=500, verbose_name=_("Title"))
    author = models.CharField(max_length=500, blank=True, verbose_name=_("Author"))
    isbn = models.CharField(
        max_length=13,
        blank=True,
        verbose_name=_("ISBN"),
        help_text=_("ISBN-10 or ISBN-13"),
    )
    cover_url = models.URLField(blank=True, verbose_name=_("Cover image URL"))
    openlibrary_id = models.CharField(
        max_length=50, blank=True, verbose_name=_("Open Library ID")
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["title"]
        verbose_name = _("Book")
        verbose_name_plural = _("Books")

    def __str__(self):
        if self.author:
            return f"{self.title} — {self.author}"
        return self.title


class BookReading(models.Model):
    """A record of reading a book to a specific child on a specific date."""

    child = models.ForeignKey(
        "core.Child",
        on_delete=models.CASCADE,
        related_name="book_readings",
        verbose_name=_("Child"),
    )
    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE,
        related_name="readings",
        verbose_name=_("Book"),
    )
    date_read = models.DateField(
        default=timezone.localdate, verbose_name=_("Date read")
    )
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        default_permissions = ("view", "add", "change", "delete")
        ordering = ["-date_read", "-created_at"]
        verbose_name = _("Book Reading")
        verbose_name_plural = _("Book Readings")

    def __str__(self):
        return f"{self.book.title} ({self.date_read})"
