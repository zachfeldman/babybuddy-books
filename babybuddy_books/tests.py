# -*- coding: utf-8 -*-
"""
Tests for the babybuddy-books plugin.

Covers: models, views (CRUD + permission gates), templatetag, and
the Open Library JSON endpoints.
"""
import json
from datetime import date, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from core.models import Child

from .models import Book, BookReading
from .templatetags.book_tags import book_card_data


def _make_child(**kwargs):
    defaults = dict(first_name="Test", last_name="Baby", birth_date=date(2023, 1, 1))
    defaults.update(kwargs)
    return Child.objects.create(**defaults)


def _make_book(**kwargs):
    defaults = dict(title="The Very Hungry Caterpillar", author="Eric Carle")
    defaults.update(kwargs)
    return Book.objects.create(**defaults)


def _make_reading(child, book, **kwargs):
    now = timezone.now()
    defaults = dict(start=now, end=now + timedelta(minutes=15))
    defaults.update(kwargs)
    return BookReading.objects.create(child=child, book=book, **defaults)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------


class BookModelTestCase(TestCase):
    def test_str_with_author(self):
        book = Book(title="Charlotte's Web", author="E.B. White")
        self.assertEqual(str(book), "Charlotte's Web — E.B. White")

    def test_str_without_author(self):
        book = Book(title="Unknown Book")
        self.assertEqual(str(book), "Unknown Book")

    def test_default_ordering_is_by_title(self):
        _make_book(title="Zebra Book")
        _make_book(title="Aardvark Book")
        titles = list(Book.objects.values_list("title", flat=True))
        self.assertEqual(titles[0], "Aardvark Book")
        self.assertEqual(titles[1], "Zebra Book")


class BookReadingModelTestCase(TestCase):
    def setUp(self):
        self.child = _make_child()
        self.book = _make_book()

    def test_str(self):
        start = timezone.now()
        reading = BookReading(child=self.child, book=self.book, start=start, end=start)
        self.assertIn(self.book.title, str(reading))

    def test_duration_computed_on_save(self):
        start = timezone.now()
        end = start + timedelta(minutes=20)
        reading = _make_reading(self.child, self.book, start=start, end=end)
        self.assertEqual(reading.duration, timedelta(minutes=20))

    def test_default_ordering_newest_first(self):
        now = timezone.now()
        r1 = _make_reading(self.child, self.book, start=now - timedelta(days=5),
                            end=now - timedelta(days=5) + timedelta(minutes=10))
        r2 = _make_reading(self.child, self.book, start=now,
                            end=now + timedelta(minutes=10))
        readings = list(BookReading.objects.values_list("id", flat=True))
        self.assertEqual(readings[0], r2.pk)  # newest first

    def test_child_deletion_cascades(self):
        _make_reading(self.child, self.book)
        self.child.delete()
        self.assertEqual(BookReading.objects.count(), 0)

    def test_book_deletion_cascades(self):
        _make_reading(self.child, self.book)
        self.book.delete()
        self.assertEqual(BookReading.objects.count(), 0)


# ---------------------------------------------------------------------------
# Template tag
# ---------------------------------------------------------------------------


class BookCardDataTestCase(TestCase):
    def setUp(self):
        self.child = _make_child()
        self.book = _make_book()

    def test_count_zero_when_no_readings(self):
        data = book_card_data(self.child)
        self.assertEqual(data["count"], 0)
        self.assertIsNone(data["last_reading"])

    def test_count_reflects_readings(self):
        now = timezone.now()
        _make_reading(self.child, self.book)
        _make_reading(self.child, self.book,
                      start=now + timedelta(days=1),
                      end=now + timedelta(days=1, minutes=15))
        data = book_card_data(self.child)
        self.assertEqual(data["count"], 2)

    def test_last_reading_is_most_recent(self):
        now = timezone.now()
        _make_reading(self.child, self.book)
        recent = _make_reading(self.child, self.book,
                               start=now + timedelta(days=30),
                               end=now + timedelta(days=30, minutes=15))
        data = book_card_data(self.child)
        self.assertEqual(data["last_reading"].pk, recent.pk)

    def test_only_counts_readings_for_given_child(self):
        other_child = _make_child(first_name="Other")
        _make_reading(other_child, self.book)
        data = book_card_data(self.child)
        self.assertEqual(data["count"], 0)


# ---------------------------------------------------------------------------
# View tests (require login + permissions)
# ---------------------------------------------------------------------------


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class BookViewsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_superuser(
            username="testuser", password="testpass", email="test@example.com"
        )
        cls.child = _make_child()
        cls.book = _make_book()

    def setUp(self):
        self.client = Client()
        self.client.login(username="testuser", password="testpass")

    def test_book_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("books:book-list"))
        self.assertNotEqual(response.status_code, 200)

    def test_book_list_renders(self):
        response = self.client.get(reverse("books:book-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.book.title)

    def test_book_add_get(self):
        response = self.client.get(reverse("books:book-add"))
        self.assertEqual(response.status_code, 200)

    def test_book_add_post(self):
        response = self.client.post(
            reverse("books:book-add"),
            {"title": "Green Eggs and Ham", "author": "Dr. Seuss"},
        )
        self.assertRedirects(response, reverse("books:book-list"))
        self.assertTrue(Book.objects.filter(title="Green Eggs and Ham").exists())

    def test_book_update(self):
        response = self.client.post(
            reverse("books:book-update", args=[self.book.pk]),
            {"title": "Updated Title", "author": "Updated Author"},
        )
        self.assertRedirects(response, reverse("books:book-list"))
        self.book.refresh_from_db()
        self.assertEqual(self.book.title, "Updated Title")

    def test_book_delete(self):
        book = _make_book(title="To Delete")
        response = self.client.post(reverse("books:book-delete", args=[book.pk]))
        self.assertRedirects(response, reverse("books:book-list"))
        self.assertFalse(Book.objects.filter(pk=book.pk).exists())

    def test_reading_list_renders(self):
        _make_reading(self.child, self.book)
        response = self.client.get(reverse("books:reading-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.book.title)

    def test_reading_list_filters_by_child(self):
        other_child = _make_child(first_name="Other")
        _make_reading(self.child, self.book)
        other_book = _make_book(title="Other Book")
        _make_reading(other_child, other_book)
        response = self.client.get(
            reverse("books:reading-list") + f"?child={self.child.slug}"
        )
        self.assertContains(response, self.book.title)
        self.assertNotContains(response, "Other Book")

    def test_reading_add_get(self):
        response = self.client.get(reverse("books:reading-add"))
        self.assertEqual(response.status_code, 200)

    def test_reading_add_post(self):
        now = timezone.now().replace(microsecond=0)
        end = now + timedelta(minutes=15)
        response = self.client.post(
            reverse("books:reading-add"),
            {
                "child": self.child.pk,
                "book": self.book.pk,
                "start": now.isoformat(),
                "end": end.isoformat(),
                "notes": "",
            },
        )
        self.assertRedirects(response, reverse("books:reading-list"))
        self.assertTrue(
            BookReading.objects.filter(child=self.child, book=self.book).exists()
        )

    def test_reading_add_prefills_child_from_query_param(self):
        response = self.client.get(
            reverse("books:reading-add") + f"?child={self.child.slug}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"].initial.get("child"), self.child)

    def test_reading_delete(self):
        reading = _make_reading(self.child, self.book)
        response = self.client.post(
            reverse("books:reading-delete", args=[reading.pk])
        )
        self.assertRedirects(response, reverse("books:reading-list"))
        self.assertFalse(BookReading.objects.filter(pk=reading.pk).exists())

    def test_reading_add_with_timer(self):
        from core.models import Timer
        timer = Timer.objects.create(user=self.user, child=self.child)
        response = self.client.get(
            reverse("books:reading-add") + f"?timer={timer.pk}"
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertEqual(form.initial.get("child"), self.child)
        self.assertIsNotNone(form.initial.get("start"))


# ---------------------------------------------------------------------------
# Open Library JSON endpoints
# ---------------------------------------------------------------------------


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class BookTitleSearchTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_superuser(
            username="testuser", password="testpass", email="test@example.com"
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username="testuser", password="testpass")

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("books:title-search") + "?q=cat")
        self.assertEqual(response.status_code, 401)

    def test_short_query_returns_empty(self):
        response = self.client.get(reverse("books:title-search") + "?q=a")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": []})

    def test_returns_empty_on_network_error(self):
        with mock.patch(
            "urllib.request.urlopen", side_effect=Exception("network error")
        ):
            response = self.client.get(
                reverse("books:title-search") + "?q=caterpillar"
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": []})

    def test_returns_results_from_open_library(self):
        fake_response = mock.MagicMock()
        fake_response.__enter__ = lambda s: s
        fake_response.__exit__ = mock.MagicMock(return_value=False)
        fake_response.read.return_value = json.dumps(
            {
                "docs": [
                    {
                        "title": "The Very Hungry Caterpillar",
                        "author_name": ["Eric Carle"],
                        "isbn": ["0399208539"],
                        "cover_i": 12345,
                        "key": "/works/OL123W",
                    }
                ]
            }
        ).encode()
        with mock.patch("urllib.request.urlopen", return_value=fake_response):
            response = self.client.get(
                reverse("books:title-search") + "?q=caterpillar"
            )
        data = response.json()
        self.assertEqual(len(data["results"]), 1)
        self.assertEqual(data["results"][0]["title"], "The Very Hungry Caterpillar")
        self.assertEqual(data["results"][0]["author"], "Eric Carle")
        self.assertEqual(data["results"][0]["isbn"], "0399208539")


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class BookIsbnLookupTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_superuser(
            username="testuser", password="testpass", email="test@example.com"
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username="testuser", password="testpass")

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("books:isbn-lookup") + "?isbn=1234567890")
        self.assertEqual(response.status_code, 401)

    def test_missing_isbn_returns_400(self):
        response = self.client.get(reverse("books:isbn-lookup"))
        self.assertEqual(response.status_code, 400)

    def test_returns_existing_db_book_without_api_call(self):
        book = _make_book(isbn="0399208539")
        with mock.patch("urllib.request.urlopen") as mock_urlopen:
            response = self.client.get(
                reverse("books:isbn-lookup") + "?isbn=0399208539"
            )
            mock_urlopen.assert_not_called()
        data = response.json()
        self.assertEqual(data["existing_id"], book.pk)
        self.assertEqual(data["title"], book.title)

    def test_returns_404_on_api_not_found(self):
        with mock.patch(
            "urllib.request.urlopen", side_effect=Exception("not found")
        ):
            response = self.client.get(
                reverse("books:isbn-lookup") + "?isbn=0000000000"
            )
        self.assertEqual(response.status_code, 404)
