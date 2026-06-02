# -*- coding: utf-8 -*-
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from babybuddy.widgets import DateTimeInput
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
        timer = kwargs.pop("timer", None)
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            from core.models import Child
            if "child" not in self.initial and Child.objects.count() == 1:
                self.initial["child"] = Child.objects.first()

            if timer is not None:
                if isinstance(timer, str):
                    from core.models import Timer
                    try:
                        timer = Timer.objects.get(pk=timer)
                    except Timer.DoesNotExist:
                        timer = None

                if timer is not None:
                    self.initial.setdefault("start", timer.start)
                    self.initial.setdefault("end", timezone.now())
                    if timer.child:
                        self.initial.setdefault("child", timer.child)
                    self._timer_id = timer.pk
                    return

        self._timer_id = None

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start")
        end = cleaned.get("end")
        if start and end and end <= start:
            self.add_error("end", _("End time must be after start time."))
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=commit)
        if commit and getattr(self, "_timer_id", None):
            from core.models import Timer
            try:
                Timer.objects.get(pk=self._timer_id).stop()
            except Timer.DoesNotExist:
                pass
        return instance

    class Meta:
        model = BookReading
        fields = ["child", "book", "start", "end", "notes"]
        widgets = {
            "child": ChildRadioSelect,
            "book": forms.HiddenInput(attrs={"data-books-book-id": "true"}),
            "start": DateTimeInput(),
            "end": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 3, "class": "form-control"}),
        }
