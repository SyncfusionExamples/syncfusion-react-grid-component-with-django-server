
# Syncfusion React Grid with Django REST Framework and Microsoft SQL Server

A lightweight, production-ready pattern for binding **Microsoft SQL Server** data to a **Syncfusion React Grid** via **Django REST Framework (DRF)**. The sample supports complete CRUD (Create, Read, Update, Delete), server-side filtering, searching, sorting, and paging using **DataManager + UrlAdaptor** with a DRF `ModelViewSet`.

## Key Features

- **SQL Server ↔ Django**: `mssql-django` + `pyodbc` connection with migrations-driven schema
- **Syncfusion React Grid**: Built-in paging, sorting, filtering, searching, and editing
- **Full CRUD**: Add, edit, and delete directly from the grid
- **Server-side Data Operations**: Read/search/filter/sort/page handled in DRF
- **Configurable Connection**: Manage credentials in `settings.py`
- **CORS-Ready**: Enable React dev origin for local development

## Prerequisites

- **Node.js** LTS (v20+), npm/yarn
- **React** 18+ (Vite)
- **Python** 3.11+
- **Django** 5.2+, **Django REST Framework**
- **Microsoft SQL Server** (or adapt to Postgres/MySQL/SQLite)


## Quick Start

### 1) Clone the repository
```bash
git clone <your-repo-url>
cd <your-project>
```

### 2) Backend (Django + DRF + MSSQL Server)
Create and activate a virtual environment, then install dependencies:
```bash
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
# source .venv/bin/activate

pip install django djangorestframework django-filter django-cors-headers mssql-django pyodbc
```

**Configure `DATABASES` in `server/settings.py`:**
```python
DATABASES = {
    "default": {
        "ENGINE": "mssql",
        "NAME": "LibraryDB",
        "USER": "django_user",
        "PASSWORD": "Django@123",
        "HOST": "(localdb)\MSSQLLocalDB",  # or your SQL host
        "OPTIONS": {
            "driver": "ODBC Driver 18 for SQL Server",
            "trustServerCertificate": "yes",  # dev only
        },
    }
}
```

Run migrations and start the API:
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 8000
```

### 3) Frontend (React + Syncfusion Grid)
Open the React app and install packages:
```bash
npm install
```

Run the React app:
```bash
npm run dev
```
Navigate to `http://localhost:5173`.

---

## Configuration

### Database Connection (Django `settings.py`)
- `ENGINE`: `"mssql"` for SQL Server via `mssql-django`
- `OPTIONS.driver`: Ensure **ODBC Driver 18 for SQL Server** is installed
- `trustServerCertificate`: set to `"yes"` only for local/dev; configure TLS properly for prod

### CORS
Allow your React dev origin during development:
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]
```

**DataManager (UrlAdaptor) behavior**
- **Read**: sends paging (`skip`, `take`), sorting (`sorted`), filtering (`where`), and searching (`search`) as JSON
- **CRUD**: sends `action: 'insert' | 'update' | 'remove'` with the appropriate payload

---

## Project Layout

| File/Folder | Purpose |
|-------------|---------|
| `server/settings.py` | Django/DRF, DB, and CORS configuration |
| `server/urls.py` | API routing with `DefaultRouter` |
| `library/models.py` | `BookLending` model |
| `library/services` | Includes services for handling server side operations |
| `library/views.py` | `ModelViewSet` exposing endpoints |
| `src/App.tsx` | React Grid + DataManager config |
| `src/index.css` | Syncfusion theme imports |

---

## Common Tasks

### Add a Record
1. Click **Add** in the grid toolbar
2. Fill out fields (title, borrower, dates, etc.)
3. Click **Save** to create the record

### Edit a Record
1. Select a row → **Edit**
2. Modify fields → **Update**

### Delete a Record
1. Select a row → **Delete**
2. Confirm deletion

### Search / Filter / Sort
- Use the **Search** box (toolbar) to match across configured columns
- Use column filter icons for equals/contains/date filters
- Click column headers to sort ascending/descending

---

## Troubleshooting

**ODBC/Driver errors**
- Install **ODBC Driver 18 for SQL Server**
- Match Python and ODBC driver architecture (64‑bit recommended)
- Verify `pyodbc` is installed and importable

**CORS blocked**
- Confirm `corsheaders` is in `INSTALLED_APPS` and middleware
- Add `http://localhost:5173` to `CORS_ALLOWED_ORIGINS`

**Migration issues**
- Run `python manage.py makemigrations && python manage.py migrate`
- Check `DATABASES` credentials and server reachability

**Date parsing/format**
- Ensure front-end date columns use `type="date"`
- If needed, configure DRF `DATETIME_INPUT_FORMATS`/`DATE_INPUT_FORMATS`

---
