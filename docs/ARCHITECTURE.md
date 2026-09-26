# CollabDocs System Architecture & Technical Specifications

This document details the software architecture, database design, transaction control strategies, signal handling, middleware pipelines, and query optimization techniques implemented in **CollabDocs**.

---

## 🏗 High-Level System Architecture

CollabDocs is engineered around a decoupled RESTful backend architecture built on Django 5.x and Django REST Framework (DRF):

```text
                               +----------------------------------+
                               |     Client / Postman / Swagger   |
                               +----------------+-----------------+
                                                |
                                                v
                               +----------------------------------+
                               |    Security & CORS Middleware    |
                               +----------------+-----------------+
                                                |
                                                v
                               +----------------------------------+
                               |    RequestLoggingMiddleware      |
                               | (High-precision timing in ms)    |
                               +----------------+-----------------+
                                                |
                                                v
                               +----------------------------------+
                               |       DRF DefaultRouter          |
                               +----------------+-----------------+
                                                |
                                                v
                               +----------------------------------+
                               |      ModelViewSets & Actions     |
                               +--------+----------------+--------+
                                        |                |
                                        v                v
                        +-------------------+   +-------------------+
                        | Serializers &     |   | transaction.atomic|
                        | Custom Validators |   | Business Logic    |
                        +-------------------+   +--------+----------+
                                                         |
                                                         v
                                                +-------------------+
                                                | PostgreSQL / DB   |
                                                +--------+----------+
                                                         |
                                                         v (post_save)
                                                +-------------------+
                                                | AuditLog Signal   |
                                                +-------------------+
```

---

## 🗄 Model Specifications & Schema Constraints

### 1. `User`

- **Purpose**: Core identity model storing user details.
- **Fields**:
  - `id`: `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`
  - `first_name`: `CharField(max_length=50)`
  - `last_name`: `CharField(max_length=50)`
  - `email`: `CharField(max_length=254, unique=True)`
  - `phone`: `CharField(max_length=15, unique=True)`
  - `created_at`: `DateTimeField(auto_now_add=True)`
- **Meta Ordering**: `['-created_at']`

### 2. `Workspace`

- **Purpose**: Logical container for documents and collaborative team members.
- **Fields**:
  - `id`: `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`
  - `name`: `CharField(max_length=255)`
  - `owner`: `ForeignKey(User, on_delete=CASCADE, related_name='owned_workspaces')`
  - `is_active`: `BooleanField(default=True)`
  - `created_at`: `DateTimeField(auto_now_add=True)`
- **Meta Ordering**: `['-created_at']`

### 3. `WorkspaceMember`

- **Purpose**: Defines user membership and access control within a workspace.
- **Fields**:
  - `id`: `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`
  - `workspace`: `ForeignKey(Workspace, on_delete=CASCADE, related_name='members')`
  - `user`: `ForeignKey(User, on_delete=CASCADE, related_name='workspace_memberships')`
  - `role`: `CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)` (`admin`, `editor`, `viewer`)
  - `joined_at`: `DateTimeField(auto_now_add=True)`
- **Constraints**: `UniqueConstraint(fields=['workspace', 'user'], name='unique_workspace_member')`

### 4. `Document`

- **Purpose**: Main content object created within workspaces.
- **Fields**:
  - `id`: `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`
  - `title`: `CharField(max_length=255)`
  - `content`: `TextField()`
  - `workspace`: `ForeignKey(Workspace, on_delete=CASCADE, related_name='documents')`
  - `created_by`: `ForeignKey(User, on_delete=SET_NULL, null=True, related_name='created_documents')`
  - `status`: `CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)` (`draft`, `published`, `archived`)
  - `updated_at`: `DateTimeField(auto_now=True)`
- **Meta Ordering**: `['-updated_at']`

### 5. `DocumentVersion`

- **Purpose**: Immutable snapshot of a document at save time.
- **Fields**:
  - `id`: `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`
  - `document`: `ForeignKey(Document, on_delete=CASCADE, related_name='versions')`
  - `content`: `TextField()`
  - `version_number`: `PositiveIntegerField()` (auto-incremented per document)
  - `saved_by`: `ForeignKey(User, on_delete=SET_NULL, null=True, related_name='document_versions')`
  - `saved_at`: `DateTimeField(auto_now_add=True)`
- **Meta Ordering**: `['version_number']`

### 6. `Comment`

- **Purpose**: Supports document discussions and nested threaded replies.
- **Fields**:
  - `id`: `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`
  - `document`: `ForeignKey(Document, on_delete=CASCADE, related_name='comments')`
  - `author`: `ForeignKey(User, on_delete=SET_NULL, null=True, related_name='comments')`
  - `content`: `TextField()`
  - `parent`: `ForeignKey('self', on_delete=SET_NULL, null=True, blank=True, related_name='replies')`
  - `created_at`: `DateTimeField(auto_now_add=True)`
- **Meta Ordering**: `['-created_at']`

### 7. `Tag`

- **Purpose**: Categorize documents across workspaces.
- **Fields**:
  - `id`: `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`
  - `name`: `CharField(max_length=100, unique=True)`
  - `documents`: `ManyToManyField(Document, related_name='tags', blank=True)`
- **Meta Ordering**: `['name']`

### 8. `AuditLog`

- **Purpose**: Automated event log tracking document creation and modification.
- **Fields**:
  - `id`: `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`
  - `actor`: `ForeignKey(User, on_delete=SET_NULL, null=True, related_name='audit_logs')`
  - `action`: `CharField(max_length=50)` (`created` | `updated`)
  - `model_name`: `CharField(max_length=100)` (`Document`)
  - `object_id`: `CharField(max_length=100)`
  - `timestamp`: `DateTimeField(auto_now_add=True)`
- **Meta Ordering**: `['-timestamp']`

---

## 🔒 Transactions & Data Integrity

CollabDocs uses `django.db.transaction.atomic()` blocks to guarantee strict database consistency for complex operations:

1. **Atomic Workspace Creation**:
   - Creating a workspace and setting its owner automatically triggers creation of a `WorkspaceMember` record with `role='admin'`.
   - If member creation fails, the workspace creation rolls back.

2. **Atomic Document Versioning**:
   - Creating a document immediately generates a `DocumentVersion` record with `version_number=1`.
   - Updating a document content generates a new `DocumentVersion` with `version_number = document.versions.count() + 1`.
   - Wrapping both operations in `transaction.atomic()` ensures version drift never occurs.

3. **Database Integrity Error Handling**:
   - Adding a member to a workspace catches `IntegrityError` caused by duplicate `(workspace, user)` pairs and returns `HTTP 409 Conflict`.

---

## ⚡ Signals & Event Infrastructure

- **Signal Receiver**: `api/signals.py` defines `create_document_audit_log` listening to `post_save` on `Document`.
- **Logic**: Evaluates the `created` boolean argument passed by Django signals:
  - If `created == True`, `action = 'created'`.
  - If `created == False`, `action = 'updated'`.
- **Signal Registration**: Imported inside `ApiConfig.ready()` in `api/apps.py` ensuring signals register seamlessly on server initialization.

---

## ⏱ Custom Request Logging Middleware

Located in `collabdocs/middleware.py`:

- **Execution Flow**:
  1. Captures start timestamp using `time.perf_counter()` (high-resolution timer).
  2. Passes request down the middleware chain via `self.get_response(request)`.
  3. Captures end timestamp and calculates `duration_ms = (end - start) * 1000.0`.
  4. Formats log string: `[{request.method}] {request.path} - Status: {response.status_code} - Time taken: {duration_ms:.2f}ms`.
  5. Outputs via Python `print()` and `logger.info()`.

---

## 🚀 Query Optimization Strategies

- **`select_related()`**: Used on foreign key relationships (`owner`, `created_by`, `saved_by`, `author`, `parent`, `workspace`) to perform SQL `JOIN`s and avoid $N+1$ query overhead.
- **`prefetch_related()`**: Used on ManyToMany relations like `Document.tags` and reverse relations like `Document.versions`.
- **`annotate(Count('members', distinct=True))`**: Aggregates workspace member counts directly at the database engine level.
- **Django `Q` Objects**: Enables complex `OR` filtering across document titles (`Q(title__icontains=search)`).
- **`distinct()`**: Used on filtered querysets to prevent duplicated results when joining across ManyToMany tables.
