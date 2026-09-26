# CollabDocs API Specification & Endpoint Guide

This document provides a comprehensive RESTful API specification for all 17 endpoints implemented in **CollabDocs** using Django REST Framework (DRF) and OpenAPI 3.0 schema generator (`drf-spectacular`).

---

## 🌐 Base URL & Header Specifications

- **Base URL**: `http://127.0.0.1:8000/api`
- **Content-Type**: `application/json`
- **Accept**: `application/json`

---

## 📋 Summary of Endpoints

| Category | Method | Endpoint | Description | Expected Status |
| :--- | :--- | :--- | :--- | :--- |
| **Users** | `POST` | `/api/users/` | Create a new user with custom validation | `201 Created` |
| | `GET` | `/api/users/{id}/` | Retrieve user details by UUID | `200 OK` / `404 Not Found` |
| **Workspaces** | `POST` | `/api/workspaces/` | Create workspace & auto-add owner as admin (atomic) | `201 Created` |
| | `GET` | `/api/workspaces/{id}/` | Get workspace details annotated with `member_count` | `200 OK` / `404 Not Found` |
| | `POST` | `/api/workspaces/{id}/members/` | Add member with role (`admin`, `editor`, `viewer`) | `201 Created` / `409 Conflict` |
| | `GET` | `/api/workspaces/{id}/members/` | List members for workspace with nested user details | `200 OK` |
| | `GET` | `/api/workspaces/{id}/summary/` | Get aggregated summary metrics for a workspace | `200 OK` |
| **Documents** | `POST` | `/api/documents/` | Create document + initial version `v1` (atomic) | `201 Created` |
| | `PUT` | `/api/documents/{id}/` | Update document content & save new version `vN` (atomic) | `200 OK` |
| | `GET` | `/api/documents/` | List documents with workspace/status/tag/search filters | `200 OK` |
| | `GET` | `/api/documents/{id}/versions/` | List all historical versions of a document | `200 OK` |
| | `GET` | `/api/documents/{id}/stats/` | Get document metrics (versions, comments, contributors) | `200 OK` |
| | `POST` | `/api/documents/{id}/tags/` | Add tags to a document (by tag ID or tag name) | `200 OK` |
| **Comments** | `POST` | `/api/comments/` | Add top-level comment or threaded reply | `201 Created` |
| | `GET` | `/api/comments/?document={id}` | List all comments for a document | `200 OK` |
| **Tags** | `POST` | `/api/tags/` | Create a unique tag | `201 Created` |
| **Audit Logs** | `GET` | `/api/audit-logs/` | Query audit log entries filtered by actor and date range | `200 OK` |

---

## 📑 Endpoint Specifications

### 1. Users

#### `POST /api/users/`

Creates a new user record.

- **Validation Rules**:
  - `phone`: Must be valid digits (10 to 15 digits, optional `+` prefix).
  - `email`: Valid email syntax and unique across users.
- **cURL Example**:

  ```bash
  curl -X POST http://127.0.0.1:8000/api/users/ \
    -H "Content-Type: application/json" \
    -d '{
      "first_name": "Alice",
      "last_name": "Smith",
      "email": "alice.smith@collabdocs.io",
      "phone": "+15551234567"
    }'
  ```

- **Response (`201 Created`)**:

  ```json
  {
    "id": "73aae619-ffb6-4bb2-ace9-977efba77b27",
    "first_name": "Alice",
    "last_name": "Smith",
    "email": "alice.smith@collabdocs.io",
    "phone": "+15551234567",
    "created_at": "2026-09-26T10:15:30.123456Z"
  }
  ```

- **Error Response (`400 Bad Request`)**:

  ```json
  {
    "phone": ["Phone number must be valid (10 to 15 digits, optional '+' prefix)."]
  }
  ```

#### `GET /api/users/{id}/`

Retrieves a user by UUID.

- **cURL Example**:

  ```bash
  curl -X GET http://127.0.0.1:8000/api/users/73aae619-ffb6-4bb2-ace9-977efba77b27/
  ```

- **Response (`200 OK`)**:

  ```json
  {
    "id": "73aae619-ffb6-4bb2-ace9-977efba77b27",
    "first_name": "Alice",
    "last_name": "Smith",
    "email": "alice.smith@collabdocs.io",
    "phone": "+15551234567",
    "created_at": "2026-09-26T10:15:30.123456Z"
  }
  ```

---

### 2. Workspaces

#### `POST /api/workspaces/`

Creates a new workspace and automatically adds the workspace owner as a `WorkspaceMember` with `role="admin"` inside a single `transaction.atomic()` block.

- **cURL Example**:

  ```bash
  curl -X POST http://127.0.0.1:8000/api/workspaces/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "Engineering Core",
      "owner": "73aae619-ffb6-4bb2-ace9-977efba77b27"
    }'
  ```

- **Response (`201 Created`)**:

  ```json
  {
    "id": "452d9876-a728-4fa0-a82e-8a38d3127ccb",
    "name": "Engineering Core",
    "owner": "73aae619-ffb6-4bb2-ace9-977efba77b27",
    "owner_detail": {
      "id": "73aae619-ffb6-4bb2-ace9-977efba77b27",
      "first_name": "Alice",
      "last_name": "Smith",
      "email": "alice.smith@collabdocs.io",
      "phone": "+15551234567",
      "created_at": "2026-09-26T10:15:30.123456Z"
    },
    "is_active": true,
    "member_count": 1,
    "created_at": "2026-09-26T10:20:00.000000Z"
  }
  ```

#### `GET /api/workspaces/{id}/`

Retrieves workspace details including `member_count` computed via Django ORM annotation (`annotate(member_count=Count('members'))`).

- **cURL Example**:

  ```bash
  curl -X GET http://127.0.0.1:8000/api/workspaces/452d9876-a728-4fa0-a82e-8a38d3127ccb/
  ```

- **Response (`200 OK`)**:

  ```json
  {
    "id": "452d9876-a728-4fa0-a82e-8a38d3127ccb",
    "name": "Engineering Core",
    "owner": "73aae619-ffb6-4bb2-ace9-977efba77b27",
    "owner_detail": {
      "id": "73aae619-ffb6-4bb2-ace9-977efba77b27",
      "first_name": "Alice",
      "last_name": "Smith",
      "email": "alice.smith@collabdocs.io",
      "phone": "+15551234567",
      "created_at": "2026-09-26T10:15:30.123456Z"
    },
    "is_active": true,
    "member_count": 2,
    "created_at": "2026-09-26T10:20:00.000000Z"
  }
  ```

#### `POST /api/workspaces/{id}/members/`

Adds a member with role (`admin`, `editor`, `viewer`) to a workspace. Enforces `UniqueConstraint(workspace, user)`.

- **cURL Example**:

  ```bash
  curl -X POST http://127.0.0.1:8000/api/workspaces/452d9876-a728-4fa0-a82e-8a38d3127ccb/members/ \
    -H "Content-Type: application/json" \
    -d '{
      "user": "96d69168-dc1b-4b94-b814-a9647354e361",
      "role": "editor"
    }'
  ```

- **Response (`201 Created`)**:

  ```json
  {
    "id": "e4d3c2b1-a099-8877-6655-4433221100ff",
    "workspace": "452d9876-a728-4fa0-a82e-8a38d3127ccb",
    "user": "96d69168-dc1b-4b94-b814-a9647354e361",
    "user_detail": {
      "id": "96d69168-dc1b-4b94-b814-a9647354e361",
      "first_name": "Bob",
      "last_name": "Jones",
      "email": "bob.jones@collabdocs.io",
      "phone": "+15559876543",
      "created_at": "2026-09-26T10:16:00.000000Z"
    },
    "role": "editor",
    "joined_at": "2026-09-26T10:22:00.000000Z"
  }
  ```

- **Duplicate Member Error (`409 Conflict`)**:

  ```json
  {
    "error": "User is already a member of this workspace."
  }
  ```

#### `GET /api/workspaces/{id}/members/`

Lists all members for a workspace with nested `user_detail` using `select_related('user')`.

- **cURL Example**:

  ```bash
  curl -X GET http://127.0.0.1:8000/api/workspaces/452d9876-a728-4fa0-a82e-8a38d3127ccb/members/
  ```

- **Response (`200 OK`)**:

  ```json
  [
    {
      "id": "e4d3c2b1-a099-8877-6655-4433221100ff",
      "workspace": "452d9876-a728-4fa0-a82e-8a38d3127ccb",
      "user": "96d69168-dc1b-4b94-b814-a9647354e361",
      "user_detail": {
        "id": "96d69168-dc1b-4b94-b814-a9647354e361",
        "first_name": "Bob",
        "last_name": "Jones",
        "email": "bob.jones@collabdocs.io",
        "phone": "+15559876543",
        "created_at": "2026-09-26T10:16:00.000000Z"
      },
      "role": "editor",
      "joined_at": "2026-09-26T10:22:00.000000Z"
    }
  ]
  ```

#### `GET /api/workspaces/{id}/summary/`

Returns aggregated summary statistics for a workspace.

- **cURL Example**:

  ```bash
  curl -X GET http://127.0.0.1:8000/api/workspaces/452d9876-a728-4fa0-a82e-8a38d3127ccb/summary/
  ```

- **Response (`200 OK`)**:

  ```json
  {
    "workspace_id": "452d9876-a728-4fa0-a82e-8a38d3127ccb",
    "workspace_name": "Engineering Core",
    "document_count": 5,
    "member_count": 3,
    "total_comments": 12
  }
  ```

---

### 3. Documents

#### `POST /api/documents/`

Creates a document and initial version `v1` inside a `transaction.atomic()` block.

- **cURL Example**:

  ```bash
  curl -X POST http://127.0.0.1:8000/api/documents/ \
    -H "Content-Type: application/json" \
    -d '{
      "title": "API Specification v1",
      "content": "Initial API documentation content",
      "workspace": "452d9876-a728-4fa0-a82e-8a38d3127ccb",
      "created_by": "73aae619-ffb6-4bb2-ace9-977efba77b27",
      "status": "draft"
    }'
  ```

- **Response (`201 Created`)**:

  ```json
  {
    "id": "36b5b8fb-3196-47e0-90e3-f21e90c1e64e",
    "title": "API Specification v1",
    "content": "Initial API documentation content",
    "workspace": "452d9876-a728-4fa0-a82e-8a38d3127ccb",
    "created_by": "73aae619-ffb6-4bb2-ace9-977efba77b27",
    "created_by_detail": {
      "id": "73aae619-ffb6-4bb2-ace9-977efba77b27",
      "first_name": "Alice",
      "last_name": "Smith",
      "email": "alice.smith@collabdocs.io",
      "phone": "+15551234567",
      "created_at": "2026-09-26T10:15:30.123456Z"
    },
    "status": "draft",
    "updated_at": "2026-09-26T10:25:00.000000Z",
    "tags": [],
    "version_count": 1
  }
  ```

#### `PUT /api/documents/{id}/`

Updates document content and automatically creates a new `DocumentVersion` (`version_number = count + 1`) inside a `transaction.atomic()` block.

- **cURL Example**:

  ```bash
  curl -X PUT http://127.0.0.1:8000/api/documents/36b5b8fb-3196-47e0-90e3-f21e90c1e64e/ \
    -H "Content-Type: application/json" \
    -d '{
      "title": "API Specification v2",
      "content": "Updated content with PostgreSQL and Redis details",
      "workspace": "452d9876-a728-4fa0-a82e-8a38d3127ccb",
      "created_by": "73aae619-ffb6-4bb2-ace9-977efba77b27",
      "status": "published"
    }'
  ```

- **Response (`200 OK`)**:

  ```json
  {
    "id": "36b5b8fb-3196-47e0-90e3-f21e90c1e64e",
    "title": "API Specification v2",
    "content": "Updated content with PostgreSQL and Redis details",
    "workspace": "452d9876-a728-4fa0-a82e-8a38d3127ccb",
    "created_by": "73aae619-ffb6-4bb2-ace9-977efba77b27",
    "status": "published",
    "updated_at": "2026-09-26T10:30:00.000000Z",
    "tags": [],
    "version_count": 2
  }
  ```

#### `GET /api/documents/`

Lists documents with support for multi-param filtering and title search.

- **Query Parameters**:
  - `workspace` (UUID): Filter by workspace ID.
  - `status` (`draft` | `published` | `archived`): Filter by document status.
  - `tag_name` (string): Filter by tag name (case-insensitive substring match).
  - `search` / `title` (string): Search in title using Django `Q` objects (`Q(title__icontains=search)`).
- **cURL Example**:

  ```bash
  curl -X GET "http://127.0.0.1:8000/api/documents/?workspace=452d9876-a728-4fa0-a82e-8a38d3127ccb&status=published&search=API"
  ```

- **Response (`200 OK`)**:

  ```json
  {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "36b5b8fb-3196-47e0-90e3-f21e90c1e64e",
        "title": "API Specification v2",
        "content": "Updated content with PostgreSQL and Redis details",
        "workspace": "452d9876-a728-4fa0-a82e-8a38d3127ccb",
        "created_by": "73aae619-ffb6-4bb2-ace9-977efba77b27",
        "status": "published",
        "updated_at": "2026-09-26T10:30:00.000000Z",
        "tags": [],
        "version_count": 2
      }
    ]
  }
  ```

#### `GET /api/documents/{id}/versions/`

Lists all historical versions of a document ordered by `version_number` ascending (`v1`, `v2`, ...).

- **cURL Example**:

  ```bash
  curl -X GET http://127.0.0.1:8000/api/documents/36b5b8fb-3196-47e0-90e3-f21e90c1e64e/versions/
  ```

- **Response (`200 OK`)**:

  ```json
  [
    {
      "id": "f1e2d3c4-b5a6-9788-7766-554433221100",
      "document": "36b5b8fb-3196-47e0-90e3-f21e90c1e64e",
      "content": "Initial API documentation content",
      "version_number": 1,
      "saved_by": "73aae619-ffb6-4bb2-ace9-977efba77b27",
      "saved_at": "2026-09-26T10:25:00.000000Z"
    },
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "document": "36b5b8fb-3196-47e0-90e3-f21e90c1e64e",
      "content": "Updated content with PostgreSQL and Redis details",
      "version_number": 2,
      "saved_by": "73aae619-ffb6-4bb2-ace9-977efba77b27",
      "saved_at": "2026-09-26T10:30:00.000000Z"
    }
  ]
  ```

#### `GET /api/documents/{id}/stats/`

Returns document metrics including total versions, comment count, and distinct contributor count across document versions, comments, and document author.

- **cURL Example**:

  ```bash
  curl -X GET http://127.0.0.1:8000/api/documents/36b5b8fb-3196-47e0-90e3-f21e90c1e64e/stats/
  ```

- **Response (`200 OK`)**:

  ```json
  {
    "document_id": "36b5b8fb-3196-47e0-90e3-f21e90c1e64e",
    "document_title": "API Specification v2",
    "version_count": 2,
    "comment_count": 4,
    "contributor_count": 3
  }
  ```

#### `POST /api/documents/{id}/tags/`

Associates existing tags by ID or creates and associates tags by name.

- **cURL Example**:

  ```bash
  curl -X POST http://127.0.0.1:8000/api/documents/36b5b8fb-3196-47e0-90e3-f21e90c1e64e/tags/ \
    -H "Content-Type: application/json" \
    -d '{
      "tag_names": ["backend", "django", "architecture"]
    }'
  ```

- **Response (`200 OK`)**:

  ```json
  {
    "id": "36b5b8fb-3196-47e0-90e3-f21e90c1e64e",
    "title": "API Specification v2",
    "content": "Updated content with PostgreSQL and Redis details",
    "workspace": "452d9876-a728-4fa0-a82e-8a38d3127ccb",
    "created_by": "73aae619-ffb6-4bb2-ace9-977efba77b27",
    "status": "published",
    "updated_at": "2026-09-26T10:30:00.000000Z",
    "tags": [
      { "id": "11111111-2222-3333-4444-555555555555", "name": "backend" },
      { "id": "66666666-7777-8888-9999-000000000000", "name": "django" },
      { "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee", "name": "architecture" }
    ],
    "version_count": 2
  }
  ```

---

### 4. Comments

#### `POST /api/comments/`

Adds a top-level comment or a threaded reply. Validates that parent comment (if provided) belongs to the exact same document.

- **cURL Example (Top-Level Comment)**:

  ```bash
  curl -X POST http://127.0.0.1:8000/api/comments/ \
    -H "Content-Type: application/json" \
    -d '{
      "document": "36b5b8fb-3196-47e0-90e3-f21e90c1e64e",
      "author": "96d69168-dc1b-4b94-b814-a9647354e361",
      "content": "Great documentation! Please add PostgreSQL pool configuration details.",
      "parent": null
    }'
  ```

- **Response (`201 Created`)**:

  ```json
  {
    "id": "c9876543-b210-4321-8765-432109876543",
    "document": "36b5b8fb-3196-47e0-90e3-f21e90c1e64e",
    "author": "96d69168-dc1b-4b94-b814-a9647354e361",
    "author_detail": {
      "id": "96d69168-dc1b-4b94-b814-a9647354e361",
      "first_name": "Bob",
      "last_name": "Jones",
      "email": "bob.jones@collabdocs.io",
      "phone": "+15559876543",
      "created_at": "2026-09-26T10:16:00.000000Z"
    },
    "content": "Great documentation! Please add PostgreSQL pool configuration details.",
    "parent": null,
    "reply_count": 0,
    "created_at": "2026-09-26T10:35:00.000000Z"
  }
  ```

- **Mismatched Parent Error (`400 Bad Request`)**:

  ```json
  {
    "parent": ["Parent comment must belong to the same document."]
  }
  ```

#### `GET /api/comments/?document={id}`

Lists all comments for a specific document using `select_related('author', 'parent', 'document')`.

- **cURL Example**:

  ```bash
  curl -X GET "http://127.0.0.1:8000/api/comments/?document=36b5b8fb-3196-47e0-90e3-f21e90c1e64e"
  ```

- **Response (`200 OK`)**:

  ```json
  {
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "c9876543-b210-4321-8765-432109876543",
        "document": "36b5b8fb-3196-47e0-90e3-f21e90c1e64e",
        "author": "96d69168-dc1b-4b94-b814-a9647354e361",
        "content": "Great documentation! Please add PostgreSQL pool configuration details.",
        "parent": null,
        "reply_count": 0,
        "created_at": "2026-09-26T10:35:00.000000Z"
      }
    ]
  }
  ```

---

### 5. Tags

#### `POST /api/tags/`

Creates a unique tag. Tag names are automatically stripped and lowercased before saving.

- **cURL Example**:

  ```bash
  curl -X POST http://127.0.0.1:8000/api/tags/ \
    -H "Content-Type: application/json" \
    -d '{
      "name": "Microservices"
    }'
  ```

- **Response (`201 Created`)**:

  ```json
  {
    "id": "ff00ee11-2233-4455-6677-8899aabbccdd",
    "name": "microservices"
  }
  ```

---

### 6. Audit Logs

#### `GET /api/audit-logs/`

Queries audit log entries generated automatically via Django `post_save` signals on `Document`. Supports filtering by `actor` ID, `date_from`, and `date_to`.

- **Query Parameters**:
  - `actor` (UUID): Filter by user ID.
  - `date_from` (ISO DateTime): Filter entries on or after this timestamp (`timestamp__gte`).
  - `date_to` (ISO DateTime): Filter entries on or before this timestamp (`timestamp__lte`).
- **cURL Example**:

  ```bash
  curl -X GET "http://127.0.0.1:8000/api/audit-logs/?actor=73aae619-ffb6-4bb2-ace9-977efba77b27&date_from=2026-09-01T00:00:00Z"
  ```

- **Response (`200 OK`)**:

  ```json
  {
    "count": 2,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": "d1e2f3a4-b5c6-7d8e-9f0a-1b2c3d4e5f6a",
        "actor": "73aae619-ffb6-4bb2-ace9-977efba77b27",
        "actor_detail": {
          "id": "73aae619-ffb6-4bb2-ace9-977efba77b27",
          "first_name": "Alice",
          "last_name": "Smith",
          "email": "alice.smith@collabdocs.io",
          "phone": "+15551234567",
          "created_at": "2026-09-26T10:15:30.123456Z"
        },
        "action": "updated",
        "model_name": "Document",
        "object_id": "36b5b8fb-3196-47e0-90e3-f21e90c1e64e",
        "timestamp": "2026-09-26T10:30:00.000000Z"
      },
      {
        "id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
        "actor": "73aae619-ffb6-4bb2-ace9-977efba77b27",
        "actor_detail": {
          "id": "73aae619-ffb6-4bb2-ace9-977efba77b27",
          "first_name": "Alice",
          "last_name": "Smith",
          "email": "alice.smith@collabdocs.io",
          "phone": "+15551234567",
          "created_at": "2026-09-26T10:15:30.123456Z"
        },
        "action": "created",
        "model_name": "Document",
        "object_id": "36b5b8fb-3196-47e0-90e3-f21e90c1e64e",
        "timestamp": "2026-09-26T10:25:00.000000Z"
      }
    ]
  }
  ```
