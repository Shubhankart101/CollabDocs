# CollabDocs Comprehensive Local Setup & Development Guide

This guide provides step-by-step instructions for setting up, running, testing, and debugging **CollabDocs** in a local environment using bare-metal Python or Docker Compose.

---

## 📋 Prerequisites & Tools

- **Python**: 3.11+
- **Pip**: Latest package installer
- **Git**: 2.30+
- **PostgreSQL**: 15+ (Optional; defaults to SQLite for local development if Postgres env variables are omitted)
- **Docker & Docker Compose**: (Optional; for containerized setup)
- **Postman**: For API testing using `CollabDocs.postman_collection.json`

---

## ⚙ Environment Variables Reference (`.env`)

Copy `.env.example` to `.env` in the root directory:

```bash
cp .env.example .env
```

| Variable Name | Default / Example Value | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | `django-insecure-key-for-dev` | Django cryptographic signing key. Change in production! |
| `DEBUG` | `True` | Enables debug mode and detailed error stack traces. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,0.0.0.0` | Comma-separated list of allowed HTTP Host headers. |
| `DB_ENGINE` | `django.db.backends.postgresql` | Set to postgresql to use Postgres, or omit for SQLite. |
| `DB_NAME` | `collabdocs` | Database name. |
| `DB_USER` | `collabuser` | Database user. |
| `DB_PASSWORD` | `collabpass` | Database password. |
| `DB_HOST` | `localhost` (or `db` in Docker) | Database hostname. |
| `DB_PORT` | `5432` | Database port. |

---

## 🛠 Option A: Bare-Metal Local Setup

### 1. Clone & Navigate to Project

```bash
git clone https://github.com/Shubhankart101/CollabDocs.git
cd CollabDocs
```

### 2. Set Up Virtual Environment

- **On Windows (PowerShell)**:

  ```powershell
  python -m venv .venv
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
  .\.venv\Scripts\Activate.ps1
  ```

- **On Linux / macOS (Bash / Zsh)**:

  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure PostgreSQL Database (Optional)

If running PostgreSQL locally, create the database and user via `psql`:

```sql
CREATE DATABASE collabdocs;
CREATE USER collabuser WITH PASSWORD 'collabpass';
ALTER ROLE collabuser SET client_encoding TO 'utf8';
ALTER ROLE collabuser SET default_transaction_isolation TO 'read committed';
ALTER ROLE collabuser SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE collabdocs TO collabuser;
```

### 5. Run Database Migrations

```bash
python manage.py makemigrations api
python manage.py migrate
```

### 6. Create Superuser (Django Admin Access)

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

- API Base Endpoint: `http://127.0.0.1:8000/api/`
- Interactive Swagger UI: `http://127.0.0.1:8000/api/schema/swagger-ui/`
- ReDoc UI: `http://127.0.0.1:8000/api/schema/redoc/`
- Django Admin Panel: `http://127.0.0.1:8000/admin/`

---

## 🐳 Option B: Docker & Docker Compose Setup

To launch the complete container stack (Django API + PostgreSQL 15 container):

### 1. Launch Containers

```bash
docker-compose up --build -d
```

### 2. View Real-Time Logs

```bash
docker-compose logs -f web
```

### 3. Run Migrations inside Container

```bash
docker-compose exec web python manage.py migrate
```

### 4. Stop & Cleanup Stack

```bash
docker-compose down -v
```

---

## 🧪 Testing & Code Coverage

### Run Automated Unit & Integration Tests

```bash
python manage.py test api
```

The suite contains **49 automated tests** (expanded from the original 26) across `test_models.py`, `test_serializers.py`, `test_signals.py`, `test_middleware.py`, and `test_views.py`. In addition to the original happy-path cases, it now also covers:

- Duplicate `email` / `phone` rejection on `User` creation (`400`).
- 404 responses for missing `User`, `Workspace`, and `Document` lookups (detail, versions, stats).
- `400`/`404` handling when adding workspace members with a missing or non-existent `user` field.
- Tag attachment via `tag_ids` in addition to `tag_names`, and `400` when neither is supplied.
- Duplicate `Tag` name rejection.
- Threaded comment replies created end-to-end via the API, including `reply_count` propagation and rejection of cross-document parent/child comments.
- `AuditLog` filtering by `date_from` / `date_to` range.
- Document list pagination response structure (`count`, `results`).
- Model-level cascade delete of `WorkspaceMember` on `Workspace` deletion, and `SET_NULL` behavior on `Document.created_by` when the referenced `User` is deleted.

#### Example Output

```text
Found 49 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.................................................
----------------------------------------------------------------------
Ran 49 tests in 0.251s

OK
Destroying test database for alias 'default'...
```

### Run Code Coverage Analysis

```bash
coverage run manage.py test api
coverage report -m
coverage html
```

---

## 📬 Postman Testing Workflow

1. Launch Postman.
2. Click **Import** -> Select `CollabDocs.postman_collection.json`.
3. Set the environment variable `baseUrl` to `http://127.0.0.1:8000/api`.
4. Run requests in recommended sequence:
   - `Users -> Create User` (copy returned `id` to `userId`)
   - `Workspaces -> Create Workspace` (copy returned `id` to `workspaceId`)
   - `Workspaces -> Add Member to Workspace`
   - `Documents -> Create Document` (copy returned `id` to `documentId`)
   - `Documents -> Update Document Content`
   - `Documents -> Add Tags to Document`
   - `Comments -> Add Comment / Reply`
   - `Audit Logs -> List Audit Logs`

The server will start at `http://127.0.0.1:8000/`.

---

## 🐳 Docker Setup

To run the application with PostgreSQL via Docker Compose:

```bash
docker-compose up --build -d
```

- API Endpoint: `http://localhost:8000/api/`
- Swagger UI: `http://localhost:8000/api/schema/swagger-ui/`

---

## 🧪 Testing

To run the complete automated test suite (49 tests covering models, views, serializers, middleware, and signals, including negative/edge-case scenarios):

```bash
python manage.py test api
```

### Example Local Test Run Output

```text
Found 49 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.................................................
----------------------------------------------------------------------
Ran 49 tests in 0.251s

OK
Destroying test database for alias 'default'...
```

To run with code coverage:

```bash
coverage run manage.py test api
coverage report -m
```

---

## 🖥️ Swagger UI & ReDoc Verification

Both interactive documentation UIs were manually verified against a live local server:

1. Started the dev server with `python manage.py runserver 127.0.0.1:8000`.
2. Opened `http://127.0.0.1:8000/api/schema/swagger-ui/` and confirmed all endpoint groups (`audit-logs`, `comments`, `documents`, `tags`, `users`, `workspaces`) render correctly — see [screenshots/swagger-ui-overview.png](screenshots/swagger-ui-overview.png).
3. Expanded `POST /api/documents/` to confirm the request/response schema renders as expected — see [screenshots/swagger-ui-create-document.png](screenshots/swagger-ui-create-document.png).
4. Used **Try it out** on `POST /api/users/` to execute a real request against the running server and received a genuine `201 Created` response — see [screenshots/swagger-ui-live-request-response.png](screenshots/swagger-ui-live-request-response.png).
5. Opened `http://127.0.0.1:8000/api/schema/redoc/` and confirmed the ReDoc alternative view renders the same schema — see [screenshots/redoc-ui-overview.png](screenshots/redoc-ui-overview.png).

---

## 📬 Postman Testing

1. Open Postman.
2. Click **Import** and select `CollabDocs.postman_collection.json` located at the root of the repository.
3. Use the pre-configured collection variables (`baseUrl`, `userId`, `workspaceId`, `documentId`) to execute requests across all 17 API endpoints.
