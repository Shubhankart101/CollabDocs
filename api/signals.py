from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Document, AuditLog


@receiver(post_save, sender=Document)
def create_document_audit_log(sender, instance, created, **kwargs):
    """
    Signal receiver that creates an AuditLog entry whenever a Document is created or updated.
    """
    action = 'created' if created else 'updated'
    actor = instance.created_by if instance.created_by else None

    AuditLog.objects.create(
        actor=actor,
        action=action,
        model_name='Document',
        object_id=str(instance.id)
    )
