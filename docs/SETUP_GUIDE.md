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

![Full verbose test run showing all 49 tests individually passing](screenshots/test-run-49-passed.png)

For the complete per-test verbose log and a worked example of a failing test, see **[docs/TESTING.md](TESTING.md)**.

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

![Full verbose test run showing all 49 tests individually passing](screenshots/test-run-49-passed.png)

For the complete per-test verbose log, a worked example of what a failing test looks like (captured live, then reverted), and the full Swagger UI live-verification walkthrough with every screenshot embedded, see the dedicated **[docs/TESTING.md](TESTING.md)**.

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

![Terminal walkthrough of clone, pip install, and migrate](screenshots/init-01-clone-install-migrate.png)

![Terminal walkthrough of runserver startup and the URLs to open](screenshots/init-02-runserver-and-urls.png)

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
6. Watch the terminal running `manage.py runserver` — the custom request-logging middleware prints a `[METHOD] path - Status - Time taken` line for every request made this way.

---

## 🖥️ Swagger UI & ReDoc Verification (Summary)

Both interactive documentation UIs were manually verified against a live local server, and the four required demo-video scenarios (atomic transaction rollback, middleware console logging, an aggregation endpoint, and the AuditLog signal) were each exercised live through Swagger UI's **Try it out** feature.

![Swagger UI overview listing all endpoint groups](screenshots/swagger-ui-overview.png)

![Live Try it out execution of POST /api/users/ returning 201 Created](screenshots/swagger-ui-live-request-response.png)

The full breakdown of each scenario — atomic rollback, middleware logging, both aggregation endpoints, the AuditLog signal, and the two real bugs found and fixed during this pass — with every screenshot embedded, lives in **[docs/TESTING.md](TESTING.md#4-live-api-verification-via-swagger-ui)**.

---

## 📬 Postman Testing

1. Open Postman.
2. Click **Import** and select `CollabDocs.postman_collection.json` located at the root of the repository.
3. Use the pre-configured collection variables (`baseUrl`, `userId`, `workspaceId`, `documentId`) to execute requests across all 17 API endpoints.
