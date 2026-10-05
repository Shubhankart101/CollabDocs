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

## ▶️ Running the App via Terminal (Cheat-Sheet)

A minimal, copy-pasteable sequence to go from a fresh clone to a running, browsable API:

```bash
# 1. Clone and enter the project
git clone https://github.com/Shubhankart101/CollabDocs.git
cd CollabDocs

# 2. Install dependencies (use a venv if you prefer, see Option A above)
pip install -r requirements.txt

# 3. Apply database migrations (SQLite by default; Postgres if .env configured)
python manage.py migrate

# 4. Start the development server
python manage.py runserver 127.0.0.1:8000
```

See [screenshots/init-01-clone-install-migrate.png](screenshots/init-01-clone-install-migrate.png) and [screenshots/init-02-runserver-and-urls.png](screenshots/init-02-runserver-and-urls.png) for a walkthrough of this exact sequence running end-to-end, including the final URLs to open.

### Opening Swagger UI / ReDoc / Admin

Once `runserver` is up, open any of the following in a browser:

| UI | URL |
| :--- | :--- |
| Swagger UI (interactive) | `http://127.0.0.1:8000/api/schema/swagger-ui/` |
| ReDoc (read-only reference) | `http://127.0.0.1:8000/api/schema/redoc/` |
| Raw OpenAPI schema | `http://127.0.0.1:8000/api/schema/` |
| Django Admin | `http://127.0.0.1:8000/admin/` |

### Testing an endpoint directly from Swagger UI

1. Click any endpoint to expand it (e.g. `POST /api/documents/`).
2. Click **Try it out**.
3. Edit the pre-filled JSON request body (and any path parameters such as `{id}`).
4. Click **Execute**.
5. Inspect the **Curl**, **Request URL**, and **Server response** sections that appear — these show the exact request sent and the live response (status code, body, headers) returned by the running server.
6. Watch the terminal running `manage.py runserver` — the custom request-logging middleware prints a `[METHOD] path - Status - Time taken` line for every request made this way (see the middleware verification below).

---

## 🖥️ Swagger UI & ReDoc Verification

Both interactive documentation UIs were manually verified against a live local server, and the four required demo-video scenarios (atomic transaction rollback, middleware console logging, an aggregation endpoint, and the AuditLog signal) were each exercised live through Swagger UI's **Try it out** feature and screenshotted.

### General UI rendering

1. Started the dev server with `python manage.py runserver 127.0.0.1:8000`.
2. Opened `http://127.0.0.1:8000/api/schema/swagger-ui/` and confirmed all endpoint groups (`audit-logs`, `comments`, `documents`, `tags`, `users`, `workspaces`) render correctly — see [screenshots/swagger-ui-overview.png](screenshots/swagger-ui-overview.png).
3. Expanded `POST /api/documents/` to confirm the request/response schema renders as expected — see [screenshots/swagger-ui-create-document.png](screenshots/swagger-ui-create-document.png).
4. Used **Try it out** on `POST /api/users/` to execute a real request against the running server and received a genuine `201 Created` response — see [screenshots/swagger-ui-live-request-response.png](screenshots/swagger-ui-live-request-response.png).
5. Opened `http://127.0.0.1:8000/api/schema/redoc/` and confirmed the ReDoc alternative view renders the same schema — see [screenshots/redoc-ui-overview.png](screenshots/redoc-ui-overview.png).

### 1. Atomic transaction with rollback on failure

`WorkspaceViewSet.members()` wraps `WorkspaceMember.objects.create(...)` in `transaction.atomic()`. Adding the same user to the same workspace twice violates the `unique_workspace_member` constraint, raising `IntegrityError` mid-transaction; the view catches it and rolls back, returning `409 Conflict` with no partial write.

1. `POST /api/workspaces/{id}/members/` with a new `user` → `201 Created` — see [screenshots/swagger-add-member-success-201.png](screenshots/swagger-add-member-success-201.png).
2. Repeating the exact same request → `409 Conflict`, `{"error": "User is already a member of this workspace."}` — see [screenshots/swagger-add-member-rollback-409.png](screenshots/swagger-add-member-rollback-409.png).
3. `GET /api/workspaces/{id}/members/` afterwards confirms the member list still has exactly the members from step 1 (no duplicate row was persisted), proving the failed transaction rolled back cleanly — see [screenshots/swagger-members-list-confirms-rollback.png](screenshots/swagger-members-list-confirms-rollback.png).

### 2. Middleware request logging in the console

`collabdocs/middleware.py`'s `RequestLoggingMiddleware` prints `[METHOD] path - Status: <code> - Time taken: <ms>ms` to the console for every request. The screenshot below is captured directly from the `runserver` console while the Swagger UI requests above were being executed — see [screenshots/middleware-request-logging-console.png](screenshots/middleware-request-logging-console.png).

### 3. Aggregation endpoints (stats / summary)

- `GET /api/documents/{id}/stats/` returns `version_count`, `comment_count`, and `contributor_count` computed via Django ORM aggregation — see [screenshots/swagger-document-stats-aggregation.png](screenshots/swagger-document-stats-aggregation.png).
- `GET /api/workspaces/{id}/summary/` returns `document_count`, `member_count`, and `total_comments` — see [screenshots/swagger-workspace-summary-aggregation.png](screenshots/swagger-workspace-summary-aggregation.png).

### 4. AuditLog written by the signal after a document update

A `post_save` signal on `Document` writes an `AuditLog` row on every create (`action="created"`) and update (`action="updated"`). After creating a document (v1) and updating it twice (v2, v3), `GET /api/audit-logs/?actor={id}` returns 3 entries: 1 `created` + 2 `updated`, each referencing the same `object_id` — see [screenshots/swagger-auditlog-signal-created-updated.png](screenshots/swagger-auditlog-signal-created-updated.png).

### Bugs found and fixed during this verification pass

While exercising the scenarios above through Swagger UI, two real issues were found and fixed (covered by new/updated automated tests):

1. **Stale `version_count` after `PUT /api/documents/{id}/`** — the `DocumentViewSet.get_queryset()` prefetches `versions`, so after creating a new `DocumentVersion` inside `update()`, the serializer's `version_count` field read the *stale* prefetch cache instead of the new count. Fixed by clearing `document._prefetched_objects_cache['versions']` before serializing the response in `api/views.py`.
2. **Undocumented filter query parameters in Swagger UI** — `workspace`/`status`/`tag_name`/`search` (documents), `document` (comments), and `actor`/`date_from`/`date_to` (audit logs) were implemented via `request.query_params` but never declared to drf-spectacular, so they were unusable from Swagger UI's **Try it out** panel. Fixed by adding `@extend_schema_view(list=extend_schema(parameters=[...]))` to `DocumentViewSet`, `CommentViewSet`, and `AuditLogViewSet` in `api/views.py`.

---

## 📬 Postman Testing

1. Open Postman.
2. Click **Import** and select `CollabDocs.postman_collection.json` located at the root of the repository.
3. Use the pre-configured collection variables (`baseUrl`, `userId`, `workspaceId`, `documentId`) to execute requests across all 17 API endpoints.
