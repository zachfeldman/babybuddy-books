# -*- coding: utf-8 -*-
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("books", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="bookreading",
            name="start",
            field=models.DateTimeField(
                default=django.utils.timezone.now,
                verbose_name="Start time",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="bookreading",
            name="end",
            field=models.DateTimeField(
                default=django.utils.timezone.now,
                verbose_name="End time",
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="bookreading",
            name="duration",
            field=models.DurationField(
                editable=False, null=True, verbose_name="Duration"
            ),
        ),
        migrations.RemoveField(
            model_name="bookreading",
            name="date_read",
        ),
        migrations.AlterModelOptions(
            name="bookreading",
            options={
                "default_permissions": ("view", "add", "change", "delete"),
                "ordering": ["-start"],
                "verbose_name": "Book Reading",
                "verbose_name_plural": "Book Readings",
            },
        ),
    ]
