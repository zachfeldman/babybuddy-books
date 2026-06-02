# -*- coding: utf-8 -*-
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0036_medication"),
    ]

    operations = [
        migrations.CreateModel(
            name="Book",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=500, verbose_name="Title")),
                (
                    "author",
                    models.CharField(blank=True, max_length=500, verbose_name="Author"),
                ),
                (
                    "isbn",
                    models.CharField(
                        blank=True,
                        help_text="ISBN-10 or ISBN-13",
                        max_length=13,
                        verbose_name="ISBN",
                    ),
                ),
                (
                    "cover_url",
                    models.URLField(blank=True, verbose_name="Cover image URL"),
                ),
                (
                    "openlibrary_id",
                    models.CharField(
                        blank=True, max_length=50, verbose_name="Open Library ID"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Book",
                "verbose_name_plural": "Books",
                "ordering": ["title"],
                "default_permissions": ("view", "add", "change", "delete"),
            },
        ),
        migrations.CreateModel(
            name="BookReading",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "date_read",
                    models.DateField(
                        default=django.utils.timezone.localdate,
                        verbose_name="Date read",
                    ),
                ),
                ("notes", models.TextField(blank=True, verbose_name="Notes")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "book",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="readings",
                        to="books.book",
                        verbose_name="Book",
                    ),
                ),
                (
                    "child",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="book_readings",
                        to="core.child",
                        verbose_name="Child",
                    ),
                ),
            ],
            options={
                "verbose_name": "Book Reading",
                "verbose_name_plural": "Book Readings",
                "ordering": ["-date_read", "-created_at"],
                "default_permissions": ("view", "add", "change", "delete"),
            },
        ),
    ]
