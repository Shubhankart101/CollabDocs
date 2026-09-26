# CollabDocs Local Setup & Testing Guide

This guide details how to set up, run, and test CollabDocs locally.

---

## 📋 Prerequisites

- **Python**: Version 3.11 or higher
- **Pip**: Latest version
- **Git**: For version control
- **Docker & Docker Compose**: Optional, for containerized execution
- **Postman**: For API testing using the included collection

---

## ⚙ Step-by-Step Setup

### 1. Clone Repository & Setup Environment

```bash
git clone https://github.com/Shubhankart101/CollabDocs.git
cd CollabDocs
cp .env.example .env
```

### 2. Virtual Environment & Dependencies

```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Run Database Migrations

```bash
python manage.py makemigrations api
python manage.py migrate
```

### 4. Run Development Server

```bash
python manage.py runserver
```

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
