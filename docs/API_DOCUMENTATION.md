# CollabDocs API Documentation

This document provides a detailed specification for all 17 RESTful API endpoints implemented in CollabDocs using Django REST Framework and `drf-spectacular`.

---

## 🔗 Overview of Endpoints

### 1. Users

#### `POST /api/users/`
- **Description**: Creates a new user in the system.
- **Request Body**:
  ```json
  {
    "first_name": "Alice",
    "last_name": "Smith",
    "email": "alice.smith@collabdocs.io",
    "phone": "+15551234567"
  }
  ```
- **Validation**:
  - `phone`: Custom validator ensuring 10-15 digits with optional `+` prefix.
  - `email`: Formatted email check & unique constraint.
- **Response**: `201 Created` with User object.

#### `GET /api/users/{id}/`
- **Description**: Retrieves user details by UUID primary key.
- **Response**: `200 OK` or `404 Not Found`.

---

### 2. Workspaces

#### `POST /api/workspaces/`
- **Description**: Creates a workspace and automatically adds the workspace owner as a `WorkspaceMember` with `role='admin'` inside a single `transaction.atomic()` block.
- **Request Body**:
  ```json
  {
    "name": "Engineering Workspace",
    "owner": "c4b189b2-3e28-4e4b-9e4a-1a2b3c4d5e6f"
  }
  ```
- **Response**: `201 Created` with Workspace object.

#### `GET /api/workspaces/{id}/`
- **Description**: Retrieves workspace details annotated with `member_count`.
- **Response**: `200 OK` or `404 Not Found`.

#### `POST /api/workspaces/{id}/members/`
- **Description**: Adds a new member with a specified role (`admin`, `editor`, `viewer`) to a workspace.
- **Request Body**:
  ```json
  {
    "user": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    "role": "editor"
  }
  ```
- **Response**: `201 Created` or `409 Conflict` (if user is already a member).

#### `GET /api/workspaces/{id}/members/`
- **Description**: Lists all members of the workspace using `select_related('user')` for optimized query performance.
- **Response**: `200 OK`.

#### `GET /api/workspaces/{id}/summary/`
- **Description**: Returns workspace summary statistics including document count, member count, and total comment count using `annotate()` and `aggregate()`.
- **Response**: `200 OK`.

---

### 3. Documents

#### `POST /api/documents/`
- **Description**: Creates a new document and initial version `v1` inside a single `transaction.atomic()` block.
- **Request Body**:
  ```json
  {
    "title": "System Architecture Specification",
    "content": "Initial document draft...",
    "workspace": "workspace-uuid",
    "created_by": "user-uuid",
    "status": "draft"
  }
  ```
- **Response**: `201 Created`.

#### `PUT /api/documents/{id}/`
- **Description**: Updates document content and automatically creates a new `DocumentVersion` (`vN`) inside a single `transaction.atomic()` block.
- **Response**: `200 OK`.

#### `GET /api/documents/`
- **Description**: Lists documents with filtering by `workspace`, `status`, `tag_name`, and search `title` (`icontains`, `Q` objects).
- **Query Parameters**: `workspace`, `status`, `tag_name`, `search` / `title`.
- **Response**: `200 OK`.

#### `GET /api/documents/{id}/versions/`
- **Description**: Lists all versions of a document in ascending order (`v1`, `v2`, ...).
- **Response**: `200 OK`.

#### `GET /api/documents/{id}/stats/`
- **Description**: Returns version count, comment count, and unique contributor count for a document.
- **Response**: `200 OK`.

#### `POST /api/documents/{id}/tags/`
- **Description**: Adds existing tags by ID or creates and associates new tags by name.
- **Request Body**:
  ```json
  {
    "tag_names": ["architecture", "django", "backend"]
  }
  ```
- **Response**: `200 OK`.

---

### 4. Comments

#### `POST /api/comments/`
- **Description**: Adds a top-level comment or threaded reply (via `parent` self-referential FK). Validates that parent comment belongs to the same document.
- **Request Body**:
  ```json
  {
    "document": "document-uuid",
    "author": "user-uuid",
    "content": "Looks good to me!",
    "parent": null
  }
  ```
- **Response**: `201 Created`.

#### `GET /api/comments/?document={id}`
- **Description**: Lists all comments for a specific document.
- **Response**: `200 OK`.

---

### 5. Tags

#### `POST /api/tags/`
- **Description**: Creates a new tag with unique name validation.
- **Response**: `201 Created`.

---

### 6. Audit Logs

#### `GET /api/audit-logs/`
- **Description**: Lists audit log entries automatically generated via `post_save` signals on `Document`. Supports filtering by `actor` ID and date range (`date_from`, `date_to`).
- **Response**: `200 OK`.
