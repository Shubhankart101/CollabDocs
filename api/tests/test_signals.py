from django.test import TestCase
from api.models import User, Workspace, Document, AuditLog


class SignalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            first_name="Signal",
            last_name="Tester",
            email="signal@example.com",
            phone="+11223344556"
        )
        self.workspace = Workspace.objects.create(
            name="Signal Workspace",
            owner=self.user
        )

    def test_document_post_save_signal_create(self):
        doc = Document.objects.create(
            title="Signal Doc",
            content="Content",
            workspace=self.workspace,
            created_by=self.user
        )
        log = AuditLog.objects.filter(object_id=str(doc.id)).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.action, "created")
        self.assertEqual(log.model_name, "Document")
        self.assertEqual(log.actor, self.user)

    def test_document_post_save_signal_update(self):
        doc = Document.objects.create(
            title="Signal Doc 2",
            content="Initial",
            workspace=self.workspace,
            created_by=self.user
        )
        doc.content = "Updated Content"
        doc.save()

        logs = AuditLog.objects.filter(object_id=str(doc.id)).order_by('timestamp')
        self.assertEqual(logs.count(), 2)
        self.assertEqual(logs[0].action, "created")
        self.assertEqual(logs[1].action, "updated")
