from django.db import transaction, IntegrityError
from django.db.models import Count, Q
from rest_framework import viewsets, status, response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiTypes

from .models import (
    User, Workspace, WorkspaceMember, Document, DocumentVersion, Comment, Tag, AuditLog
)
from .serializers import (
    UserSerializer,
    WorkspaceSerializer,
    WorkspaceMemberSerializer,
    WorkspaceSummarySerializer,
    DocumentSerializer,
    DocumentVersionSerializer,
    DocumentStatsSerializer,
    CommentSerializer,
    TagSerializer,
    AuditLogSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for User CRUD endpoints.
    - POST /api/users/ : Create user
    - GET /api/users/{id}/ : Get user by ID
    """
    queryset = User.objects.all().order_by('-created_at')
    serializer_class = UserSerializer


class WorkspaceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Workspace endpoints.
    - POST /api/workspaces/ : Create workspace + auto-add owner as admin member (atomic)
    - GET /api/workspaces/{id}/ : Get workspace with member count
    - POST /api/workspaces/{id}/members/ : Add member with role
    - GET /api/workspaces/{id}/members/ : List all members with nested user detail
    - GET /api/workspaces/{id}/summary/ : Workspace aggregate stats
    """
    queryset = Workspace.objects.all().order_by('-created_at')
    serializer_class = WorkspaceSerializer

    def get_queryset(self):
        return Workspace.objects.select_related('owner').annotate(
            member_count=Count('members', distinct=True)
        ).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """
        Create workspace and automatically add owner as WorkspaceMember with role='admin' in a transaction.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            workspace = serializer.save()
            WorkspaceMember.objects.create(
                workspace=workspace,
                user=workspace.owner,
                role=WorkspaceMember.Role.ADMIN
            )

        headers = self.get_success_headers(serializer.data)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @extend_schema(
        summary="Manage members of a workspace (GET to list, POST to add)",
        methods=['GET', 'POST'],
        request=WorkspaceMemberSerializer,
        responses={
            200: WorkspaceMemberSerializer(many=True),
            201: WorkspaceMemberSerializer,
            409: OpenApiTypes.OBJECT
        }
    )
    @action(detail=True, methods=['get', 'post'], url_path='members')
    def members(self, request, pk=None):
        workspace = self.get_object()

        if request.method == 'GET':
            members_qs = WorkspaceMember.objects.filter(workspace=workspace).select_related('user').order_by('-joined_at')
            serializer = WorkspaceMemberSerializer(members_qs, many=True)
            return response.Response(serializer.data, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            user_id = request.data.get('user')
            role = request.data.get('role', WorkspaceMember.Role.VIEWER)

            if not user_id:
                return response.Response(
                    {"error": "Field 'user' is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return response.Response(
                    {"error": f"User with ID {user_id} does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )

            try:
                with transaction.atomic():
                    member = WorkspaceMember.objects.create(
                        workspace=workspace,
                        user=user,
                        role=role
                    )
                    serializer = WorkspaceMemberSerializer(member)
                    return response.Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return response.Response(
                    {"error": "User is already a member of this workspace."},
                    status=status.HTTP_409_CONFLICT
                )

    @extend_schema(
        summary="Get workspace summary stats",
        responses={200: WorkspaceSummarySerializer}
    )
    @action(detail=True, methods=['get'], url_path='summary')
    def summary(self, request, pk=None):
        workspace = self.get_object()
        doc_count = workspace.documents.count()
        member_count = workspace.members.count()
        total_comments = Comment.objects.filter(document__workspace=workspace).count()

        summary_data = {
            'workspace_id': workspace.id,
            'workspace_name': workspace.name,
            'document_count': doc_count,
            'member_count': member_count,
            'total_comments': total_comments,
        }
        serializer = WorkspaceSummarySerializer(summary_data)
        return response.Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary="List documents with optional filters",
        parameters=[
            OpenApiParameter(name='workspace', type=OpenApiTypes.UUID, description='Filter documents by workspace ID.'),
            OpenApiParameter(name='status', type=OpenApiTypes.STR, description='Filter by document status: draft, published, archived.'),
            OpenApiParameter(name='tag_name', type=OpenApiTypes.STR, description='Filter documents that have a tag matching this name (icontains).'),
            OpenApiParameter(name='search', type=OpenApiTypes.STR, description='Search documents by title (icontains).'),
        ]
    )
)
class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Document endpoints.
    - POST /api/documents/ : Create document + first version (atomic)
    - PUT /api/documents/{id}/ : Update document content - saves new version (atomic)
    - GET /api/documents/ : List documents - filter by workspace, status, tag_name, search title
    - GET /api/documents/{id}/versions/ : All versions in order
    - GET /api/documents/{id}/stats/ : Version, comment, and contributor counts
    - POST /api/documents/{id}/tags/ : Add tags to document
    """
    queryset = Document.objects.all().order_by('-updated_at')
    serializer_class = DocumentSerializer

    def get_queryset(self):
        queryset = Document.objects.select_related('workspace', 'created_by').prefetch_related('tags', 'versions')

        workspace_id = self.request.query_params.get('workspace')
        doc_status = self.request.query_params.get('status')
        tag_name = self.request.query_params.get('tag_name')
        search_title = self.request.query_params.get('search') or self.request.query_params.get('title')

        if workspace_id:
            queryset = queryset.filter(workspace_id=workspace_id)
        if doc_status:
            queryset = queryset.filter(status=doc_status)
        if tag_name:
            queryset = queryset.filter(tags__name__icontains=tag_name)
        if search_title:
            queryset = queryset.filter(Q(title__icontains=search_title))

        return queryset.distinct()

    def create(self, request, *args, **kwargs):
        """
        Create document and initial DocumentVersion (v1) inside a transaction.atomic() block.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            document = serializer.save()
            DocumentVersion.objects.create(
                document=document,
                content=document.content,
                version_number=1,
                saved_by=document.created_by
            )

        headers = self.get_success_headers(serializer.data)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        """
        Update document content and create a new DocumentVersion inside a transaction.atomic() block.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            document = serializer.save()
            # Calculate next version number per document
            next_version = document.versions.count() + 1
            saved_by_user = document.created_by
            if 'saved_by' in request.data:
                try:
                    saved_by_user = User.objects.get(id=request.data['saved_by'])
                except User.DoesNotExist:
                    pass

            DocumentVersion.objects.create(
                document=document,
                content=document.content,
                version_number=next_version,
                saved_by=saved_by_user
            )

        # Clear the prefetched 'versions' cache so version_count reflects the newly created version
        if hasattr(document, '_prefetched_objects_cache'):
            document._prefetched_objects_cache.pop('versions', None)

        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(summary="Get all versions of a document")
    @action(detail=True, methods=['get'], url_path='versions')
    def list_versions(self, request, pk=None):
        document = self.get_object()
        versions = DocumentVersion.objects.filter(document=document).select_related('saved_by').order_by('version_number')
        serializer = DocumentVersionSerializer(versions, many=True)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Get document statistics",
        responses={200: DocumentStatsSerializer}
    )
    @action(detail=True, methods=['get'], url_path='stats')
    def stats(self, request, pk=None):
        document = self.get_object()
        version_count = document.versions.count()
        comment_count = document.comments.count()
        # Unique contributors from document versions + comments + creator
        version_contributors = document.versions.values_list('saved_by', flat=True)
        comment_contributors = document.comments.values_list('author', flat=True)
        all_contributors = set(filter(None, list(version_contributors) + list(comment_contributors)))
        if document.created_by_id:
            all_contributors.add(document.created_by_id)

        stats_data = {
            'document_id': document.id,
            'document_title': document.title,
            'version_count': version_count,
            'comment_count': comment_count,
            'contributor_count': len(all_contributors),
        }
        serializer = DocumentStatsSerializer(stats_data)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Add tags to a document",
        request=OpenApiTypes.OBJECT,
        responses={200: DocumentSerializer}
    )
    @action(detail=True, methods=['post'], url_path='tags')
    def add_tags(self, request, pk=None):
        document = self.get_object()
        tag_ids = request.data.get('tag_ids', [])
        tag_names = request.data.get('tag_names', [])

        tags_to_add = []
        if tag_ids:
            tags_to_add.extend(Tag.objects.filter(id__in=tag_ids))
        if tag_names:
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name.strip().lower())
                tags_to_add.append(tag)

        if not tags_to_add:
            return response.Response(
                {"error": "Provide at least 'tag_ids' or 'tag_names'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        for tag in tags_to_add:
            tag.documents.add(document)

        serializer = self.get_serializer(document)
        return response.Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        summary="List comments, optionally filtered by document",
        parameters=[
            OpenApiParameter(name='document', type=OpenApiTypes.UUID, description='Filter comments belonging to this document ID.'),
        ]
    )
)
class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Comment endpoints.
    - POST /api/comments/ : Add comment or reply
    - GET /api/comments/?document={id} : List all comments for a document
    """
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer

    def get_queryset(self):
        queryset = Comment.objects.select_related('author', 'parent', 'document')
        document_id = self.request.query_params.get('document')
        if document_id:
            queryset = queryset.filter(document_id=document_id)
        return queryset.order_by('-created_at')


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Tag endpoints.
    - POST /api/tags/ : Create a tag
    - GET /api/tags/ : List tags
    """
    queryset = Tag.objects.all().order_by('name')
    serializer_class = TagSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List audit logs filtered by actor and/or date range",
        parameters=[
            OpenApiParameter(name='actor', type=OpenApiTypes.UUID, description='Filter audit logs created by this actor/user ID.'),
            OpenApiParameter(name='date_from', type=OpenApiTypes.DATETIME, description='Only include logs with a timestamp on/after this ISO-8601 datetime.'),
            OpenApiParameter(name='date_to', type=OpenApiTypes.DATETIME, description='Only include logs with a timestamp on/before this ISO-8601 datetime.'),
        ]
    )
)
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for AuditLog endpoints.
    - GET /api/audit-logs/ : List audit logs filtered by actor ID and date range
    """
    queryset = AuditLog.objects.all().order_by('-timestamp')
    serializer_class = AuditLogSerializer

    def get_queryset(self):
        queryset = AuditLog.objects.select_related('actor')
        actor_id = self.request.query_params.get('actor')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')

        if actor_id:
            queryset = queryset.filter(actor_id=actor_id)
        if date_from:
            queryset = queryset.filter(timestamp__gte=date_from)
        if date_to:
            queryset = queryset.filter(timestamp__lte=date_to)

        return queryset
