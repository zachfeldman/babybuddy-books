# -*- coding: utf-8 -*-
from babybuddy.plugins import BabyBuddyPluginConfig


class BooksConfig(BabyBuddyPluginConfig):
    name = "babybuddy_books"
    label = "books"
    verbose_name = "Books"

    babybuddy_nav_label = "Readings"
    babybuddy_nav_url_name = "books:reading-list"
    babybuddy_nav_icon = "icon-note"
    babybuddy_nav_group = "activities"
    babybuddy_activity_url_name = "books:reading-add"
    babybuddy_activity_label = "Reading"

    # Dashboard: summary card (templates/books/cards/summary.html)
    babybuddy_has_dashboard_card = True

    # API: /api/books/ and /api/book-readings/
    babybuddy_has_api = True

    # Timer: adds "Reading" button on the timer detail page
    babybuddy_timer_activities = [
        {
            "permission": "books.add_bookreading",
            "url_name": "books:reading-add",
            "label": "Reading",
            "icon": "icon-note",
        }
    ]
