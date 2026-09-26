# CollabDocs System Architecture & Database Design

This document describes the architectural decisions, database models, signal mechanisms, and middleware implemented in CollabDocs.

---

## 🏗 High-Level Architecture Overview

CollabDocs follows Django's Model-View-Template pattern adapted for RESTful APIs using Django REST Framework (DRF):

```text
                        +----------------------------+
                        |     HTTP Client / Postman  |
                        +--------------+-------------+
                                       |
                                       v
                        +----------------------------+
                        | RequestLoggingMiddleware   |
                        +--------------+-------------+
                                       |
                                       v
                        +----------------------------+
                        |    DRF Routers & ViewSets  |
                        +--------------+-------------+
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
        +--------------------+                   +-------------------+
        | Serializers & Val. |                   |  Atomic Services  |
        +--------------------+                   +---------+---------+
                                                           |
                                                           v
                                                 +-------------------+
                                                 | PostgreSQL / DB   |
                                                 +---------+---------+
                                                           |
                                                           v (post_save)
                                                 +-------------------+
                                                 | AuditLog Signal   |
                                                 +-------------------+
```

---

## 🗄 Database Models & Constraints

### 1. `User`

- **Fields**: `id` (UUID, PK), `first_name`, `last_name`, `email` (unique), `phone` (unique), `created_at`.
- **Primary Key**: `uuid.uuid4`, `editable=False`.

### 2. `Workspace`

- **Fields**: `id` (UUID, PK), `name`, `owner` (FK -> `User`), `is_active` (default=True), `created_at`.

### 3. `WorkspaceMember`

- **Fields**: `id` (UUID, PK), `workspace` (FK -> `Workspace`), `user` (FK -> `User`), `role` (`admin`, `editor`, `viewer`), `joined_at`.
- **Constraint**: `models.UniqueConstraint(fields=['workspace', 'user'], name='unique_workspace_member')`.

### 4. `Document`

- **Fields**: `id` (UUID, PK), `title`, `content`, `workspace` (FK -> `Workspace`), `created_by` (FK -> `User`), `status` (`draft`, `published`, `archived`), `updated_at`.

### 5. `DocumentVersion`

- **Fields**: `id` (UUID, PK), `document` (FK -> `Document`), `content`, `version_number` (per-document increment), `saved_by` (FK -> `User`), `saved_at`.

### 6. `Comment`

- **Fields**: `id` (UUID, PK), `document` (FK -> `Document`), `author` (FK -> `User`), `content`, `parent` (FK -> `self`), `created_at`.

### 7. `Tag`

- **Fields**: `id` (UUID, PK), `name` (unique), `documents` (`ManyToManyField` -> `Document`).

### 8. `AuditLog`

- **Fields**: `id` (UUID, PK), `actor` (FK -> `User`), `action`, `model_name`, `object_id`, `timestamp`.

---

## ⚡ Middleware & Signals

### Request Logging Middleware

- Located in `collabdocs/middleware.py`.
- Intercepts incoming requests, records start time via `time.perf_counter()`, calls `get_response()`, records end time, and prints:
  `[HTTP_METHOD] /path - Status: STATUS_CODE - Time taken: XX.XXms`

### AuditLog Post-Save Signal

- Located in `api/signals.py`.
- Connected to `post_save` on `Document`.
- Automatically logs document creation (`action='created'`) and document modification (`action='updated'`).
