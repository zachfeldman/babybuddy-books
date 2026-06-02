# -*- coding: utf-8 -*-
from django import template

from babybuddy_books.models import BookReading

register = template.Library()


@register.simple_tag
def book_card_data(child):
    """
    Returns a dict with reading stats for a child.
    Used by templates/books/cards/summary.html.

    Usage: {% book_card_data child as data %}
    """
    readings = BookReading.objects.filter(child=child).select_related("book")
    last = readings.first()
    return {
        "count": readings.count(),
        "last_reading": last,
    }
