# -*- coding: utf-8 -*-
import json
import urllib.parse
import urllib.request

from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import ListView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from babybuddy.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .forms import BookForm, BookReadingForm
from .models import Book, BookReading

OPENLIBRARY_SEARCH = "https://openlibrary.org/search.json"
OPENLIBRARY_COVERS = "https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"


# ---------------------------------------------------------------------------
# Book CRUD
# ---------------------------------------------------------------------------


class BookList(PermissionRequiredMixin, ListView):
    model = Book
    template_name = "books/book_list.html"
    permission_required = ("books.view_book",)
    paginate_by = 50
    ordering = ["title"]


class BookAdd(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = "books/book_form.html"
    permission_required = ("books.add_book",)
    success_url = reverse_lazy("books:book-list")
    success_message = _("Book added!")


class BookUpdate(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = "books/book_form.html"
    permission_required = ("books.change_book",)
    success_url = reverse_lazy("books:book-list")
    success_message = _("Book updated!")


class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    template_name = "books/book_confirm_delete.html"
    permission_required = ("books.delete_book",)
    success_url = reverse_lazy("books:book-list")


# ---------------------------------------------------------------------------
# BookReading CRUD
# ---------------------------------------------------------------------------


class BookReadingList(PermissionRequiredMixin, ListView):
    model = BookReading
    template_name = "books/reading_list.html"
    permission_required = ("books.view_bookreading",)
    paginate_by = 50

    def get_queryset(self):
        qs = super().get_queryset().select_related("book", "child")
        child_slug = self.request.GET.get("child")
        if child_slug:
            qs = qs.filter(child__slug=child_slug)
        return qs

    def get_context_data(self, **kwargs):
        from core.models import Child

        ctx = super().get_context_data(**kwargs)
        ctx["children"] = Child.objects.all()
        ctx["selected_child"] = self.request.GET.get("child", "")
        return ctx


class BookReadingAdd(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = BookReading
    form_class = BookReadingForm
    template_name = "books/reading_form.html"
    permission_required = ("books.add_bookreading",)
    success_url = reverse_lazy("books:reading-list")
    success_message = _("Reading logged!")

    def get_initial(self):
        initial = super().get_initial()
        child_slug = self.request.GET.get("child")
        if child_slug:
            from core.models import Child
            try:
                initial["child"] = Child.objects.get(slug=child_slug)
            except Child.DoesNotExist:
                pass
        book_pk = self.request.GET.get("book")
        if book_pk:
            try:
                initial["book"] = Book.objects.get(pk=book_pk)
            except Book.DoesNotExist:
                pass
        return initial


class BookReadingUpdate(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = BookReading
    form_class = BookReadingForm
    template_name = "books/reading_form.html"
    permission_required = ("books.change_bookreading",)
    success_url = reverse_lazy("books:reading-list")
    success_message = _("Reading updated!")


class BookReadingDelete(PermissionRequiredMixin, DeleteView):
    model = BookReading
    template_name = "books/reading_confirm_delete.html"
    permission_required = ("books.delete_bookreading",)
    success_url = reverse_lazy("books:reading-list")


# ---------------------------------------------------------------------------
# Open Library JSON endpoints (used by the book form JS)
# ---------------------------------------------------------------------------


def book_local_search(request):
    """GET /books/search/?q=<query> — search existing books in local DB."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "login required"}, status=401)

    q = request.GET.get("q", "").strip()
    qs = Book.objects.order_by("title")
    if q:
        qs = qs.filter(title__icontains=q)
    books = qs[:20]
    return JsonResponse({
        "results": [
            {
                "id": b.pk,
                "title": b.title,
                "author": b.author,
                "isbn": b.isbn,
                "cover_url": b.cover_url,
            }
            for b in books
        ]
    })


def book_quick_add(request):
    """POST /books/quick-add/ — create a book from scanned/looked-up data, return its id."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "login required"}, status=401)
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    import json as _json
    try:
        data = _json.loads(request.body)
    except Exception:
        return JsonResponse({"error": "invalid JSON"}, status=400)

    isbn = data.get("isbn", "").strip()
    # Re-use existing book if ISBN matches
    if isbn:
        existing = Book.objects.filter(isbn=isbn).first()
        if existing:
            return JsonResponse({"id": existing.pk, "title": existing.title, "author": existing.author, "cover_url": existing.cover_url})

    book = Book.objects.create(
        title=data.get("title", "").strip() or "Unknown",
        author=data.get("author", "").strip(),
        isbn=isbn,
        cover_url=data.get("cover_url", "").strip(),
        openlibrary_id=data.get("openlibrary_id", "").strip(),
    )
    return JsonResponse({"id": book.pk, "title": book.title, "author": book.author, "cover_url": book.cover_url})


def book_title_search(request):
    """GET /books/title-search/?q=<query> — autocomplete from Open Library."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "login required"}, status=401)

    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    params = urllib.parse.urlencode(
        {"q": q, "fields": "title,author_name,isbn,cover_i,key", "limit": 8}
    )
    try:
        with urllib.request.urlopen(
            f"{OPENLIBRARY_SEARCH}?{params}", timeout=4
        ) as resp:
            data = json.loads(resp.read())
    except Exception:
        return JsonResponse({"results": []})

    results = []
    for doc in data.get("docs", []):
        isbn_list = doc.get("isbn", [])
        results.append(
            {
                "title": doc.get("title", ""),
                "author": ", ".join(doc.get("author_name", [])),
                "isbn": isbn_list[0] if isbn_list else "",
                "cover_url": (
                    f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-M.jpg"
                    if doc.get("cover_i")
                    else ""
                ),
                "openlibrary_id": doc.get("key", ""),
            }
        )
    return JsonResponse({"results": results})


def book_isbn_lookup(request):
    """GET /books/isbn-lookup/?isbn=<isbn> — fetch metadata by ISBN."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "login required"}, status=401)

    isbn = request.GET.get("isbn", "").strip().replace("-", "").replace(" ", "")
    if not isbn:
        return JsonResponse({"error": "isbn required"}, status=400)

    # Return existing DB record if we already know this book
    existing = Book.objects.filter(isbn=isbn).first()
    if existing:
        return JsonResponse(
            {
                "title": existing.title,
                "author": existing.author,
                "isbn": existing.isbn,
                "cover_url": existing.cover_url,
                "openlibrary_id": existing.openlibrary_id,
                "existing_id": existing.pk,
            }
        )

    # Fetch from Open Library
    try:
        with urllib.request.urlopen(
            f"https://openlibrary.org/isbn/{isbn}.json", timeout=4
        ) as resp:
            data = json.loads(resp.read())
    except Exception:
        return JsonResponse({"error": "not found"}, status=404)

    # Resolve author names (each is a separate API call; cap at 2)
    authors = []
    for author_ref in data.get("authors", [])[:2]:
        key = author_ref.get("key", "")
        try:
            with urllib.request.urlopen(
                f"https://openlibrary.org{key}.json", timeout=3
            ) as r:
                authors.append(json.loads(r.read()).get("name", ""))
        except Exception:
            pass

    return JsonResponse(
        {
            "title": data.get("title", ""),
            "author": ", ".join(authors),
            "isbn": isbn,
            "cover_url": OPENLIBRARY_COVERS.format(isbn=isbn),
            "openlibrary_id": data.get("key", ""),
        }
    )
