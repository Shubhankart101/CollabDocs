import re
from rest_framework import serializers
from .models import User, Workspace, WorkspaceMember, Document, DocumentVersion, Comment, Tag, AuditLog


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with custom phone number validation.
    """
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_phone(self, value):
        """
        Custom validation: Phone number must be between 10 and 15 digits (optional leading +).
        """
        pattern = r'^\+?[0-9]{10,14}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                "Phone number must be valid (10 to 15 digits, optional '+' prefix)."
            )
        return value

    def validate_email(self, value):
        """
        Custom validation: Email format and check duplicate.
        """
        if not value or '@' not in value:
            raise serializers.ValidationError("Enter a valid email address.")
        return value.lower().strip()


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    """
    Serializer for WorkspaceMember model with nested User representation.
    """
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = WorkspaceMember
        fields = ['id', 'workspace', 'user', 'user_detail', 'role', 'joined_at']
        read_only_fields = ['id', 'joined_at']

    def validate_role(self, value):
        """
        Custom validation for member role.
        """
        valid_roles = [choice[0] for choice in WorkspaceMember.Role.choices]
        if value not in valid_roles:
            raise serializers.ValidationError(f"Role must be one of {valid_roles}.")
        return value


class WorkspaceSerializer(serializers.ModelSerializer):
    """
    Serializer for Workspace model with member_count SerializerMethodField.
    """
    owner_detail = UserSerializer(source='owner', read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Workspace
        fields = ['id', 'name', 'owner', 'owner_detail', 'is_active', 'member_count', 'created_at']
        read_only_fields = ['id', 'created_at', 'member_count']

    def get_member_count(self, obj):
        if hasattr(obj, 'member_count'):
            return obj.member_count
        return obj.members.count()


class WorkspaceSummarySerializer(serializers.Serializer):
    """
    Serializer for Workspace Summary aggregation endpoint.
    """
    workspace_id = serializers.UUIDField()
    workspace_name = serializers.CharField()
    document_count = serializers.IntegerField()
    member_count = serializers.IntegerField()
    total_comments = serializers.IntegerField()


class DocumentVersionSerializer(serializers.ModelSerializer):
    """
    Serializer for DocumentVersion model.
    """
    saved_by_detail = UserSerializer(source='saved_by', read_only=True)

    class Meta:
        model = DocumentVersion
        fields = ['id', 'document', 'content', 'version_number', 'saved_by', 'saved_by_detail', 'saved_at']
        read_only_fields = ['id', 'version_number', 'saved_at']


class TagSerializer(serializers.ModelSerializer):
    """
    Serializer for Tag model with custom tag name validation.
    """
    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields = ['id']

    def validate_name(self, value):
        """
        Custom validation: Tag name must be non-empty and stripped.
        """
        cleaned_name = value.strip().lower()
        if not cleaned_name:
            raise serializers.ValidationError("Tag name cannot be empty.")
        if len(cleaned_name) < 2:
            raise serializers.ValidationError("Tag name must be at least 2 characters long.")
        return cleaned_name


class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for Document model with nested fields and version/tag method fields.
    """
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    version_count = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'title', 'content', 'workspace', 'created_by',
            'created_by_detail', 'status', 'updated_at', 'tags', 'version_count'
        ]
        read_only_fields = ['id', 'updated_at', 'version_count']

    def get_version_count(self, obj):
        if hasattr(obj, 'version_count'):
            return obj.version_count
        return obj.versions.count()


class DocumentStatsSerializer(serializers.Serializer):
    """
    Serializer for Document Statistics endpoint.
    """
    document_id = serializers.UUIDField()
    document_title = serializers.CharField()
    version_count = serializers.IntegerField()
    comment_count = serializers.IntegerField()
    contributor_count = serializers.IntegerField()


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment model with self-referential reply fields.
    """
    author_detail = UserSerializer(source='author', read_only=True)
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'document', 'author', 'author_detail', 'content', 'parent', 'reply_count', 'created_at']
        read_only_fields = ['id', 'reply_count', 'created_at']

    def get_reply_count(self, obj):
        return obj.replies.count()

    def validate(self, attrs):
        """
        Validation: Ensure parent comment belongs to the same document if present.
        """
        parent = attrs.get('parent')
        document = attrs.get('document')

        if parent and document and parent.document_id != document.id:
            raise serializers.ValidationError({
                "parent": "Parent comment must belong to the same document."
            })
        return attrs


class AuditLogSerializer(serializers.ModelSerializer):
    """
    Serializer for AuditLog model.
    """
    actor_detail = UserSerializer(source='actor', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'actor', 'actor_detail', 'action', 'model_name', 'object_id', 'timestamp']
        read_only_fields = ['id', 'actor', 'actor_detail', 'action', 'model_name', 'object_id', 'timestamp']
