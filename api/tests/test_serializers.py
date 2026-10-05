from django.test import TestCase
from rest_framework.exceptions import ValidationError
from api.models import User, Workspace, Document, Comment
from api.serializers import (
    UserSerializer,
    CommentSerializer,
    TagSerializer,
    WorkspaceMemberSerializer,
)


class SerializerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            phone="+12345678901"
        )
        self.workspace = Workspace.objects.create(
            name="Test WS",
            owner=self.user
        )
        self.doc1 = Document.objects.create(
            title="Doc 1",
            content="Content 1",
            workspace=self.workspace,
            created_by=self.user
        )
        self.doc2 = Document.objects.create(
            title="Doc 2",
            content="Content 2",
            workspace=self.workspace,
            created_by=self.user
        )

    def test_user_serializer_valid_phone(self):
        serializer = UserSerializer(data={
            "first_name": "Valid",
            "last_name": "Phone",
            "email": "validphone@example.com",
            "phone": "+19876543210"
        })
        self.assertTrue(serializer.is_valid())

    def test_user_serializer_invalid_phone(self):
        serializer = UserSerializer(data={
            "first_name": "Invalid",
            "last_name": "Phone",
            "email": "invalidphone@example.com",
            "phone": "short"
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("phone", serializer.errors)

    def test_user_serializer_invalid_email(self):
        serializer = UserSerializer(data={
            "first_name": "Invalid",
            "last_name": "Email",
            "email": "notanemail",
            "phone": "+12345678999"
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_workspace_member_invalid_role(self):
        serializer = WorkspaceMemberSerializer(data={
            "workspace": str(self.workspace.id),
            "user": str(self.user.id),
            "role": "superadmin"
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("role", serializer.errors)

    def test_tag_serializer_name_cleaning(self):
        serializer = TagSerializer(data={"name": "  PYTHON-DJANGO  "})
        self.assertTrue(serializer.is_valid())
        tag = serializer.save()
        self.assertEqual(tag.name, "python-django")

    def test_tag_serializer_short_name(self):
        serializer = TagSerializer(data={"name": "a"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("name", serializer.errors)

    def test_comment_serializer_mismatched_parent_document(self):
        parent_comment = Comment.objects.create(
            document=self.doc1,
            author=self.user,
            content="Doc 1 comment"
        )
        serializer = CommentSerializer(data={
            "document": str(self.doc2.id),
            "author": str(self.user.id),
            "content": "Reply to doc 1 comment on doc 2",
            "parent": str(parent_comment.id)
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn("parent", serializer.errors)

    def test_comment_serializer_valid_same_document_parent(self):
        parent_comment = Comment.objects.create(
            document=self.doc1,
            author=self.user,
            content="Doc 1 parent comment"
        )
        serializer = CommentSerializer(data={
            "document": str(self.doc1.id),
            "author": str(self.user.id),
            "content": "Valid reply on same document",
            "parent": str(parent_comment.id)
        })
        self.assertTrue(serializer.is_valid())

    def test_workspace_member_valid_role(self):
        serializer = WorkspaceMemberSerializer(data={
            "workspace": str(self.workspace.id),
            "user": str(self.user.id),
            "role": "editor"
        })
        self.assertTrue(serializer.is_valid())

    def test_user_serializer_missing_required_fields(self):
        serializer = UserSerializer(data={"first_name": "OnlyFirst"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("last_name", serializer.errors)
        self.assertIn("email", serializer.errors)
        self.assertIn("phone", serializer.errors)
