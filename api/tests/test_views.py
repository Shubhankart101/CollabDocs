from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from api.models import User, Workspace, WorkspaceMember, Document, DocumentVersion, Comment, Tag, AuditLog


class ViewsTestCase(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create(
            first_name="Owner",
            last_name="User",
            email="owner@example.com",
            phone="+12345678900"
        )
        self.user2 = User.objects.create(
            first_name="Member",
            last_name="User",
            email="member@example.com",
            phone="+12345678901"
        )

    # 1 & 2: Users endpoints
    def test_create_and_get_user(self):
        url = reverse('user-list')
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "phone": "+19998887766"
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user_id = res.data['id']

        detail_url = reverse('user-detail', kwargs={'pk': user_id})
        res_get = self.client.get(detail_url)
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(res_get.data['first_name'], "John")

    def test_user_invalid_phone_validation(self):
        url = reverse('user-list')
        data = {
            "first_name": "Invalid",
            "last_name": "Phone",
            "email": "invalid@example.com",
            "phone": "abc123"
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('phone', res.data)

    # 3, 4, 5, 6, 7: Workspaces endpoints
    def test_workspace_creation_auto_admin(self):
        url = reverse('workspace-list')
        data = {
            "name": "Acme Corp",
            "owner": str(self.user1.id)
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        ws_id = res.data['id']

        # Verify owner was auto-added as WorkspaceMember with role='admin'
        members = WorkspaceMember.objects.filter(workspace_id=ws_id)
        self.assertEqual(members.count(), 1)
        self.assertEqual(members.first().role, WorkspaceMember.Role.ADMIN)

    def test_workspace_detail_and_members(self):
        ws = Workspace.objects.create(name="Engineering", owner=self.user1)
        WorkspaceMember.objects.create(workspace=ws, user=self.user1, role=WorkspaceMember.Role.ADMIN)

        # GET detail
        detail_url = reverse('workspace-detail', kwargs={'pk': ws.id})
        res = self.client.get(detail_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['member_count'], 1)

        # POST Add member
        add_mem_url = reverse('workspace-members', kwargs={'pk': ws.id})
        res_add = self.client.post(add_mem_url, {"user": str(self.user2.id), "role": "editor"}, format='json')
        self.assertEqual(res_add.status_code, status.HTTP_201_CREATED)

        # Duplicate member -> 409 Conflict
        res_dup = self.client.post(add_mem_url, {"user": str(self.user2.id), "role": "viewer"}, format='json')
        self.assertEqual(res_dup.status_code, status.HTTP_409_CONFLICT)

        # GET List members
        list_mem_url = reverse('workspace-members', kwargs={'pk': ws.id})
        res_list = self.client.get(list_mem_url)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_list.data), 2)

    def test_workspace_summary(self):
        ws = Workspace.objects.create(name="Summary WS", owner=self.user1)
        WorkspaceMember.objects.create(workspace=ws, user=self.user1, role=WorkspaceMember.Role.ADMIN)
        doc = Document.objects.create(title="Doc 1", content="Content", workspace=ws, created_by=self.user1)
        Comment.objects.create(document=doc, author=self.user1, content="Hello")

        url = reverse('workspace-summary', kwargs={'pk': ws.id})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['document_count'], 1)
        self.assertEqual(res.data['member_count'], 1)
        self.assertEqual(res.data['total_comments'], 1)

    # 8, 9, 10, 11, 12, 13: Documents endpoints
    def test_document_create_and_versioning(self):
        ws = Workspace.objects.create(name="Docs WS", owner=self.user1)

        # POST Document creates initial version (v1)
        url = reverse('document-list')
        data = {
            "title": "Architecture Doc",
            "content": "Version 1 Content",
            "workspace": str(ws.id),
            "created_by": str(self.user1.id),
            "status": "draft"
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        doc_id = res.data['id']

        versions = DocumentVersion.objects.filter(document_id=doc_id)
        self.assertEqual(versions.count(), 1)
        self.assertEqual(versions.first().version_number, 1)

        # PUT Document updates content and creates version (v2)
        detail_url = reverse('document-detail', kwargs={'pk': doc_id})
        update_data = {
            "title": "Architecture Doc Updated",
            "content": "Version 2 Content",
            "workspace": str(ws.id),
            "created_by": str(self.user1.id),
            "status": "published"
        }
        res_put = self.client.put(detail_url, update_data, format='json')
        self.assertEqual(res_put.status_code, status.HTTP_200_OK)

        versions_after = DocumentVersion.objects.filter(document_id=doc_id).order_by('version_number')
        self.assertEqual(versions_after.count(), 2)
        self.assertEqual(versions_after[1].version_number, 2)
        self.assertEqual(versions_after[1].content, "Version 2 Content")

        # Regression: response's version_count must reflect the newly created version (not a stale prefetch cache)
        self.assertEqual(res_put.data['version_count'], 2)

    def test_document_list_filtering(self):
        ws = Workspace.objects.create(name="Filter WS", owner=self.user1)
        doc1 = Document.objects.create(title="Python Best Practices", content="Content", workspace=ws, created_by=self.user1, status="published")
        doc2 = Document.objects.create(title="Django Guide", content="Content", workspace=ws, created_by=self.user1, status="draft")
        tag = Tag.objects.create(name="python")
        tag.documents.add(doc1)

        url = reverse('document-list')

        # Filter by status
        res_status = self.client.get(f"{url}?status=published")
        self.assertEqual(len(res_status.data['results']), 1)

        # Filter by search title
        res_search = self.client.get(f"{url}?search=Django")
        self.assertEqual(len(res_search.data['results']), 1)

        # Filter by tag_name
        res_tag = self.client.get(f"{url}?tag_name=python")
        self.assertEqual(len(res_tag.data['results']), 1)

    def test_document_versions_stats_tags(self):
        ws = Workspace.objects.create(name="Stats WS", owner=self.user1)
        doc = Document.objects.create(title="Stats Doc", content="Content", workspace=ws, created_by=self.user1)
        DocumentVersion.objects.create(document=doc, content="v1", version_number=1, saved_by=self.user1)

        # Versions list
        versions_url = reverse('document-list-versions', kwargs={'pk': doc.id})
        res_v = self.client.get(versions_url)
        self.assertEqual(res_v.status_code, status.HTTP_200_OK)

        # Stats
        stats_url = reverse('document-stats', kwargs={'pk': doc.id})
        res_s = self.client.get(stats_url)
        self.assertEqual(res_s.status_code, status.HTTP_200_OK)
        self.assertIn('version_count', res_s.data)

        # Add tags
        tags_url = reverse('document-add-tags', kwargs={'pk': doc.id})
        res_t = self.client.post(tags_url, {"tag_names": ["backend", "django"]}, format='json')
        self.assertEqual(res_t.status_code, status.HTTP_200_OK)
        self.assertEqual(doc.tags.count(), 2)

    # 14, 15: Comments endpoints
    def test_comments(self):
        ws = Workspace.objects.create(name="Comment WS", owner=self.user1)
        doc = Document.objects.create(title="Comment Doc", content="Content", workspace=ws, created_by=self.user1)

        url = reverse('comment-list')
        comment_data = {
            "document": str(doc.id),
            "author": str(self.user1.id),
            "content": "Great document!"
        }
        res = self.client.post(url, comment_data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        # GET filter by document
        res_get = self.client.get(f"{url}?document={doc.id}")
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)

    # 16: Tags endpoint
    def test_tags(self):
        url = reverse('tag-list')
        res = self.client.post(url, {"name": "microservices"}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    # 17: Audit logs endpoint
    def test_audit_logs(self):
        ws = Workspace.objects.create(name="Audit WS", owner=self.user1)
        Document.objects.create(title="Audit Doc", content="Content", workspace=ws, created_by=self.user1)

        url = reverse('auditlog-list')
        res = self.client.get(f"{url}?actor={self.user1.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_audit_logs_date_range_filter(self):
        ws = Workspace.objects.create(name="Audit Range WS", owner=self.user1)
        Document.objects.create(title="Range Doc", content="Content", workspace=ws, created_by=self.user1)

        url = reverse('auditlog-list')
        res_future = self.client.get(f"{url}?date_from=2999-01-01T00:00:00Z")
        self.assertEqual(res_future.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_future.data['results']), 0)

        res_past = self.client.get(f"{url}?date_to=1999-01-01T00:00:00Z")
        self.assertEqual(res_past.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_past.data['results']), 0)

    # --- Additional edge-case and negative scenarios ---

    def test_user_duplicate_email_rejected(self):
        url = reverse('user-list')
        data = {
            "first_name": "Dup",
            "last_name": "Email",
            "email": self.user1.email,
            "phone": "+15550001111"
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_duplicate_phone_rejected(self):
        url = reverse('user-list')
        data = {
            "first_name": "Dup",
            "last_name": "Phone",
            "email": "unique@example.com",
            "phone": self.user1.phone
        }
        res = self.client.post(url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_nonexistent_user_returns_404(self):
        url = reverse('user-detail', kwargs={'pk': '11111111-1111-1111-1111-111111111111'})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_add_member_missing_user_field_returns_400(self):
        ws = Workspace.objects.create(name="Missing Field WS", owner=self.user1)
        url = reverse('workspace-members', kwargs={'pk': ws.id})
        res = self.client.post(url, {"role": "editor"}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_member_nonexistent_user_returns_404(self):
        ws = Workspace.objects.create(name="Bad User WS", owner=self.user1)
        url = reverse('workspace-members', kwargs={'pk': ws.id})
        res = self.client.post(
            url, {"user": "11111111-1111-1111-1111-111111111111", "role": "editor"}, format='json'
        )
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_nonexistent_workspace_returns_404(self):
        url = reverse('workspace-detail', kwargs={'pk': '11111111-1111-1111-1111-111111111111'})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_document_create_missing_required_fields_returns_400(self):
        url = reverse('document-list')
        res = self.client.post(url, {"title": "No Workspace Doc"}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_document_versions_and_stats_for_nonexistent_document_returns_404(self):
        bad_id = '11111111-1111-1111-1111-111111111111'
        versions_url = reverse('document-list-versions', kwargs={'pk': bad_id})
        res_v = self.client.get(versions_url)
        self.assertEqual(res_v.status_code, status.HTTP_404_NOT_FOUND)

        stats_url = reverse('document-stats', kwargs={'pk': bad_id})
        res_s = self.client.get(stats_url)
        self.assertEqual(res_s.status_code, status.HTTP_404_NOT_FOUND)

    def test_document_add_tags_with_tag_ids(self):
        ws = Workspace.objects.create(name="Tag IDs WS", owner=self.user1)
        doc = Document.objects.create(title="Tag IDs Doc", content="Content", workspace=ws, created_by=self.user1)
        tag = Tag.objects.create(name="infrastructure")

        tags_url = reverse('document-add-tags', kwargs={'pk': doc.id})
        res = self.client.post(tags_url, {"tag_ids": [str(tag.id)]}, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(doc.tags.count(), 1)

    def test_document_add_tags_without_payload_returns_400(self):
        ws = Workspace.objects.create(name="No Tags WS", owner=self.user1)
        doc = Document.objects.create(title="No Tags Doc", content="Content", workspace=ws, created_by=self.user1)

        tags_url = reverse('document-add-tags', kwargs={'pk': doc.id})
        res = self.client.post(tags_url, {}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_document_stats_contributor_count(self):
        ws = Workspace.objects.create(name="Contributor WS", owner=self.user1)
        doc = Document.objects.create(title="Contributor Doc", content="Content", workspace=ws, created_by=self.user1)
        DocumentVersion.objects.create(document=doc, content="v2", version_number=2, saved_by=self.user2)
        Comment.objects.create(document=doc, author=self.user2, content="Nice work")

        stats_url = reverse('document-stats', kwargs={'pk': doc.id})
        res = self.client.get(stats_url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Contributors: creator (user1) + version saver (user2) + comment author (user2) = 2 unique
        self.assertEqual(res.data['contributor_count'], 2)

    def test_threaded_comment_reply_via_api(self):
        ws = Workspace.objects.create(name="Reply WS", owner=self.user1)
        doc = Document.objects.create(title="Reply Doc", content="Content", workspace=ws, created_by=self.user1)

        url = reverse('comment-list')
        parent_res = self.client.post(
            url, {"document": str(doc.id), "author": str(self.user1.id), "content": "Parent comment"}, format='json'
        )
        self.assertEqual(parent_res.status_code, status.HTTP_201_CREATED)
        parent_id = parent_res.data['id']

        reply_res = self.client.post(
            url,
            {
                "document": str(doc.id),
                "author": str(self.user2.id),
                "content": "Reply comment",
                "parent": parent_id,
            },
            format='json',
        )
        self.assertEqual(reply_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(reply_res.data['parent']), parent_id)

        # Parent's reply_count should now reflect the new reply
        get_res = self.client.get(f"{url}?document={doc.id}")
        parent_entry = next(c for c in get_res.data['results'] if c['id'] == parent_id)
        self.assertEqual(parent_entry['reply_count'], 1)

    def test_comment_reply_cross_document_returns_400(self):
        ws = Workspace.objects.create(name="Cross Doc WS", owner=self.user1)
        doc1 = Document.objects.create(title="Doc A", content="Content", workspace=ws, created_by=self.user1)
        doc2 = Document.objects.create(title="Doc B", content="Content", workspace=ws, created_by=self.user1)
        parent = Comment.objects.create(document=doc1, author=self.user1, content="Parent on Doc A")

        url = reverse('comment-list')
        res = self.client.post(
            url,
            {
                "document": str(doc2.id),
                "author": str(self.user2.id),
                "content": "Invalid cross-document reply",
                "parent": str(parent.id),
            },
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tag_duplicate_name_rejected(self):
        url = reverse('tag-list')
        self.client.post(url, {"name": "backend"}, format='json')
        res = self.client.post(url, {"name": "backend"}, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_document_list_pagination_structure(self):
        ws = Workspace.objects.create(name="Pagination WS", owner=self.user1)
        for i in range(3):
            Document.objects.create(title=f"Doc {i}", content="Content", workspace=ws, created_by=self.user1)

        url = reverse('document-list')
        res = self.client.get(f"{url}?workspace={ws.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('count', res.data)
        self.assertIn('results', res.data)
        self.assertEqual(res.data['count'], 3)
