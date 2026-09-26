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
