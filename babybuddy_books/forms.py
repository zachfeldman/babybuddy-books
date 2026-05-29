# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import gettext_lazy as _

from core.widgets import ChildRadioSelect

from .models import Book, BookReading


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ["title", "author", "isbn", "cover_url"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "data-books-autocomplete": "title",
                    "placeholder": _("Start typing a title…"),
                }
            ),
            "isbn": forms.TextInput(
                attrs={
                    "autocomplete": "off",
                    "data-books-isbn-input": "true",
                    "placeholder": _("ISBN-10 or ISBN-13"),
                }
            ),
        }


class BookReadingForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default to the only child when adding a new reading
        if not self.instance.pk and "child" not in self.initial:
            from core.models import Child
            if Child.objects.count() == 1:
                self.initial["child"] = Child.objects.first()

    class Meta:
        model = BookReading
        fields = ["child", "book", "date_read", "notes"]
        widgets = {
            "child": ChildRadioSelect,
            # Hidden — the reading form renders a custom searchable UI above this
            "book": forms.HiddenInput(attrs={"data-books-book-id": "true"}),
            "date_read": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }
