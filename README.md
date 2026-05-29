# django-babybuddy-books

A [Baby Buddy](https://github.com/babybuddy/babybuddy) plugin for tracking books read to your child.

## Features

- Log books read to each child with date and notes
- Dashboard card showing total books read + last book
- Book library with title autocomplete via Open Library
- ISBN lookup + camera scanning on mobile
- REST API endpoints for books and readings

## Installation

### Via pip (production / HA addon)

```bash
pip install django-babybuddy-books
```

Baby Buddy auto-discovers the plugin via the `babybuddy.plugins` entry point —
no `INSTALLED_APPS` edit needed. Then run migrations:

```bash
python manage.py migrate
```

### Local development

```bash
pip install -e /path/to/babybuddy-books
python manage.py migrate
```

## Home Assistant Addon

In the Baby Buddy addon configuration, add to the `plugins` list:

```yaml
plugins:
  - django-babybuddy-books
```

Restart the addon. Migrations run automatically on startup.
