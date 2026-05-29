# -*- coding: utf-8 -*-
from babybuddy.plugins import BabyBuddyPluginConfig


class BooksConfig(BabyBuddyPluginConfig):
    name = "babybuddy_books"
    label = "books"
    verbose_name = "Books"

    # Nav: top-level "Readings" link inserted after Timeline
    babybuddy_nav_label = "Readings"
    babybuddy_nav_url_name = "books:reading-list"
    babybuddy_nav_icon = "icon-note"

    # Dashboard: summary card (templates/books/cards/summary.html)
    babybuddy_has_dashboard_card = True

    # API: /api/books/ and /api/book-readings/
    babybuddy_has_api = True
