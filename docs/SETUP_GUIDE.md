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

#### Example Output

```text
Found 26 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
[GET] /api/users/ - Status: 200 - Time taken: 0.39ms
...............[GET] /api/audit-logs/ - Status: 200 - Time taken: 32.37ms
.[POST] /api/comments/ - Status: 201 - Time taken: 5.80ms
[GET] /api/comments/ - Status: 200 - Time taken: 8.85ms
.[POST] /api/users/ - Status: 201 - Time taken: 2.51ms
[GET] /api/users/b42e76a1-69b3-43d8-9999-92a83420d1cd/ - Status: 200 - Time taken: 3.17ms
.[POST] /api/documents/ - Status: 201 - Time taken: 11.23ms
[PUT] /api/documents/f5a46e8f-c3ad-4dcf-b205-7403b32e5b3c/ - Status: 200 - Time taken: 11.12ms
.[GET] /api/documents/ - Status: 200 - Time taken: 9.75ms
[GET] /api/documents/ - Status: 200 - Time taken: 7.62ms
[GET] /api/documents/ - Status: 200 - Time taken: 11.50ms
.[GET] /api/documents/608ba5c2-7899-45fa-99a8-629dec543fd6/versions/ - Status: 200 - Time taken: 11.55ms
[GET] /api/documents/608ba5c2-7899-45fa-99a8-629dec543fd6/stats/ - Status: 200 - Time taken: 10.94ms
[POST] /api/documents/608ba5c2-7899-45fa-99a8-629dec543fd6/tags/ - Status: 200 - Time taken: 9.27ms
.[POST] /api/tags/ - Status: 201 - Time taken: 1.98ms
.[POST] /api/users/ - Status: 400 - Time taken: 1.94ms
.[POST] /api/workspaces/ - Status: 201 - Time taken: 4.50ms
.[GET] /api/workspaces/0f977bcc-7d61-4249-9cb1-f9d53df4230c/ - Status: 200 - Time taken: 5.61ms
[POST] /api/workspaces/0f977bcc-7d61-4249-9cb1-f9d53df4230c/members/ - Status: 201 - Time taken: 7.79ms
[POST] /api/workspaces/0f977bcc-7d61-4249-9cb1-f9d53df4230c/members/ - Status: 409 - Time taken: 4.62ms
[GET] /api/workspaces/0f977bcc-7d61-4249-9cb1-f9d53df4230c/members/ - Status: 200 - Time taken: 6.10ms
.[GET] /api/workspaces/5ab8ecec-7e66-4241-ba21-255e9991afd0/summary/ - Status: 200 - Time taken: 4.00ms
.
----------------------------------------------------------------------
Ran 26 tests in 0.409s

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

To run the complete automated test suite (26 tests covering models, views, serializers, middleware, and signals):

```bash
python manage.py test api
```

### Example Local Test Run Output

```text
Found 26 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
[GET] /api/users/ - Status: 200 - Time taken: 0.39ms
...............[GET] /api/audit-logs/ - Status: 200 - Time taken: 32.37ms
.[POST] /api/comments/ - Status: 201 - Time taken: 5.80ms
[GET] /api/comments/ - Status: 200 - Time taken: 8.85ms
.[POST] /api/users/ - Status: 201 - Time taken: 2.51ms
[GET] /api/users/b42e76a1-69b3-43d8-9999-92a83420d1cd/ - Status: 200 - Time taken: 3.17ms
.[POST] /api/documents/ - Status: 201 - Time taken: 11.23ms
[PUT] /api/documents/f5a46e8f-c3ad-4dcf-b205-7403b32e5b3c/ - Status: 200 - Time taken: 11.12ms
.[GET] /api/documents/ - Status: 200 - Time taken: 9.75ms
[GET] /api/documents/ - Status: 200 - Time taken: 7.62ms
[GET] /api/documents/ - Status: 200 - Time taken: 11.50ms
.[GET] /api/documents/608ba5c2-7899-45fa-99a8-629dec543fd6/versions/ - Status: 200 - Time taken: 11.55ms
[GET] /api/documents/608ba5c2-7899-45fa-99a8-629dec543fd6/stats/ - Status: 200 - Time taken: 10.94ms
[POST] /api/documents/608ba5c2-7899-45fa-99a8-629dec543fd6/tags/ - Status: 200 - Time taken: 9.27ms
.[POST] /api/tags/ - Status: 201 - Time taken: 1.98ms
.[POST] /api/users/ - Status: 400 - Time taken: 1.94ms
.[POST] /api/workspaces/ - Status: 201 - Time taken: 4.50ms
.[GET] /api/workspaces/0f977bcc-7d61-4249-9cb1-f9d53df4230c/ - Status: 200 - Time taken: 5.61ms
[POST] /api/workspaces/0f977bcc-7d61-4249-9cb1-f9d53df4230c/members/ - Status: 201 - Time taken: 7.79ms
[POST] /api/workspaces/0f977bcc-7d61-4249-9cb1-f9d53df4230c/members/ - Status: 409 - Time taken: 4.62ms
[GET] /api/workspaces/0f977bcc-7d61-4249-9cb1-f9d53df4230c/members/ - Status: 200 - Time taken: 6.10ms
.[GET] /api/workspaces/5ab8ecec-7e66-4241-ba21-255e9991afd0/summary/ - Status: 200 - Time taken: 4.00ms
.
----------------------------------------------------------------------
Ran 26 tests in 0.409s

OK
Destroying test database for alias 'default'...
```

To run with code coverage:

```bash
coverage run manage.py test api
coverage report -m
```

---

## 📬 Postman Testing

1. Open Postman.
2. Click **Import** and select `CollabDocs.postman_collection.json` located at the root of the repository.
3. Use the pre-configured collection variables (`baseUrl`, `userId`, `workspaceId`, `documentId`) to execute requests across all 17 API endpoints.
