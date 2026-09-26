import uuid
from django.db import models


class User(models.Model):
    """
    User model as specified:
    - primary key: UUIDField with auto-generation (uuid4), editable=False
    - email: CharField (max 254), unique=True
    - phone: CharField (max 15), unique=True
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.CharField(max_length=254, unique=True)
    phone = models.CharField(max_length=15, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"


class Workspace(models.Model):
    """
    Workspace model:
    - owner: FK -> User (on_delete=CASCADE)
    - is_active: BooleanField (default=True)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='owned_workspaces'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class WorkspaceMember(models.Model):
    """
    WorkspaceMember model:
    - TextChoices for role: admin, editor, viewer
    - UniqueConstraint on (workspace, user)
    """
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        EDITOR = 'editor', 'Editor'
        VIEWER = 'viewer', 'Viewer'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name='members'
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='workspace_memberships'
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['workspace', 'user'], name='unique_workspace_member'
            )
        ]

    def __str__(self):
        return f"{self.user} in {self.workspace} ({self.role})"


class Document(models.Model):
    """
    Document model:
    - TextChoices for status: draft, published, archived
    - created_by: FK -> User (SET_NULL)
    """
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'
        ARCHIVED = 'archived', 'Archived'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    workspace = models.ForeignKey(
        Workspace, on_delete=models.CASCADE, related_name='documents'
    )
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='created_documents'
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class DocumentVersion(models.Model):
    """
    DocumentVersion model:
    - Snapshot of document content at save time
    - version_number: auto-increment per document
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name='versions'
    )
    content = models.TextField()
    version_number = models.PositiveIntegerField()
    saved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='document_versions'
    )
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['version_number']

    def __str__(self):
        return f"{self.document.title} - v{self.version_number}"


class Comment(models.Model):
    """
    Comment model:
    - Self-referential FK parent for threaded replies
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name='comments'
    )
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='comments'
    )
    content = models.TextField()
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.document}"


class Tag(models.Model):
    """
    Tag model:
    - ManyToManyField with Document (related_name='tags')
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    documents = models.ManyToManyField(
        Document, related_name='tags', blank=True
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class AuditLog(models.Model):
    """
    AuditLog model:
    - Automatically created via post_save signal on Document
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='audit_logs'
    )
    action = models.CharField(max_length=50)
    model_name = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp}] {self.actor} - {self.action} {self.model_name}({self.object_id})"
