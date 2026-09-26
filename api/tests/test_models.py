from django.test import TestCase
from django.db import IntegrityError
from api.models import User, Workspace, WorkspaceMember, Document, DocumentVersion, Comment, Tag, AuditLog


class ModelTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            phone="+12345678901"
        )
        self.user2 = User.objects.create(
            first_name="Bob",
            last_name="Jones",
            email="bob@example.com",
            phone="+19876543210"
        )
        self.workspace = Workspace.objects.create(
            name="Dev Workspace",
            owner=self.user1
        )

    def test_user_creation(self):
        self.assertEqual(str(self.user1), "Alice Smith (alice@example.com)")
        self.assertIsNotNone(self.user1.id)

    def test_unique_workspace_member_constraint(self):
        WorkspaceMember.objects.create(
            workspace=self.workspace,
            user=self.user2,
            role=WorkspaceMember.Role.EDITOR
        )
        with self.assertRaises(IntegrityError):
            WorkspaceMember.objects.create(
                workspace=self.workspace,
                user=self.user2,
                role=WorkspaceMember.Role.VIEWER
            )

    def test_document_and_version(self):
        doc = Document.objects.create(
            title="Design Spec",
            content="Initial Content",
            workspace=self.workspace,
            created_by=self.user1,
            status=Document.Status.DRAFT
        )
        version = DocumentVersion.objects.create(
            document=doc,
            content=doc.content,
            version_number=1,
            saved_by=self.user1
        )
        self.assertEqual(doc.versions.count(), 1)
        self.assertEqual(version.version_number, 1)

    def test_comment_self_referential(self):
        doc = Document.objects.create(
            title="API Guide",
            content="Content",
            workspace=self.workspace,
            created_by=self.user1
        )
        parent_comment = Comment.objects.create(
            document=doc,
            author=self.user1,
            content="Top level comment"
        )
        reply = Comment.objects.create(
            document=doc,
            author=self.user2,
            content="Reply comment",
            parent=parent_comment
        )
        self.assertEqual(parent_comment.replies.count(), 1)
        self.assertEqual(reply.parent, parent_comment)

    def test_tag_many_to_many(self):
        doc = Document.objects.create(
            title="Tagged Doc",
            content="Content",
            workspace=self.workspace,
            created_by=self.user1
        )
        tag = Tag.objects.create(name="python")
        tag.documents.add(doc)
        self.assertIn(doc, tag.documents.all())
        self.assertIn(tag, doc.tags.all())
