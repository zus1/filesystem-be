from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from filesystem.models import Node, NodeTypes


class BaseNodeTest(TestCase):
    """
    Patches all signal-level filesystem I/O so tests don't touch disk.
    os.path.exists returns True so the delete branch always proceeds
    (rmtree/remove are themselves mocked to no-ops).
    """

    def setUp(self):
        self.client = APIClient()
        self._patches = [
            patch('filesystem.signals.os.path.exists', return_value=True),
            patch('filesystem.signals.os.mkdir'),
            patch('filesystem.signals.os.chmod'),
            patch('filesystem.signals._touch'),
            patch('filesystem.signals.shutil.rmtree'),
            patch('filesystem.signals.os.remove'),
        ]
        for p in self._patches:
            p.start()
        self.addCleanup(patch.stopall)

    def _make_folder(self, name, parent=None):
        return Node.objects.create(original_name=name, type=NodeTypes.FOLDER, parent=parent)

    def _make_file(self, name, parent=None):
        return Node.objects.create(original_name=name, type=NodeTypes.FILE, parent=parent)


# ---------------------------------------------------------------------------
# POST /api/nodes/  — create
# ---------------------------------------------------------------------------

class NodesViewSetCreateTests(BaseNodeTest):

    def setUp(self):
        super().setUp()
        self.url = reverse('nodes-view-set-create')

    def test_create_root_folder_returns_201(self):
        response = self.client.post(
            self.url,
            {'original_name': 'documents', 'type': 'FOLDER', 'parent': None},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['original_name'], 'documents')
        self.assertEqual(response.data['type'], NodeTypes.FOLDER)
        self.assertIsNone(response.data['parent'])

    def test_create_root_file_returns_201(self):
        response = self.client.post(
            self.url,
            {'original_name': 'readme.txt', 'type': 'FILE', 'parent': None},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['original_name'], 'readme.txt')
        self.assertEqual(response.data['type'], NodeTypes.FILE)
        # FILE nodes receive a generated unique name; FOLDER nodes do not
        self.assertIsNotNone(response.data['name'])

    def test_create_child_folder_returns_201(self):
        parent = self._make_folder('documents')
        response = self.client.post(
            self.url,
            {'original_name': 'reports', 'type': 'FOLDER', 'parent': parent.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['parent'], parent.id)

    def test_create_child_file_returns_201(self):
        parent = self._make_folder('documents')
        response = self.client.post(
            self.url,
            {'original_name': 'notes.txt', 'type': 'FILE', 'parent': parent.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['parent'], parent.id)
        self.assertIsNotNone(response.data['name'])

    def test_create_persists_node_to_database(self):
        self.client.post(
            self.url,
            {'original_name': 'photos', 'type': 'FOLDER', 'parent': None},
            format='json',
        )
        self.assertTrue(Node.objects.filter(original_name='photos').exists())

    def test_create_duplicate_root_name_returns_400(self):
        self._make_folder('documents')
        response = self.client.post(
            self.url,
            {'original_name': 'documents', 'type': 'FOLDER', 'parent': None},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_duplicate_name_in_same_parent_returns_400(self):
        parent = self._make_folder('documents')
        self._make_folder('reports', parent=parent)
        response = self.client.post(
            self.url,
            {'original_name': 'reports', 'type': 'FOLDER', 'parent': parent.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_same_name_allowed_in_different_parents_returns_201(self):
        parent1 = self._make_folder('documents')
        parent2 = self._make_folder('photos')
        self._make_folder('reports', parent=parent1)
        response = self.client.post(
            self.url,
            {'original_name': 'reports', 'type': 'FOLDER', 'parent': parent2.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_with_nonexistent_parent_returns_404(self):
        response = self.client.post(
            self.url,
            {'original_name': 'reports', 'type': 'FOLDER', 'parent': 99999},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# GET /api/nodes/<id>/  — retrieve
# ---------------------------------------------------------------------------

class NodesViewSetRetrieveTests(BaseNodeTest):

    def test_retrieve_existing_node_returns_200(self):
        node = self._make_folder('documents')
        url = reverse('nodes-view-set-detail', kwargs={'id': node.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], node.id)
        self.assertEqual(response.data['original_name'], 'documents')

    def test_retrieve_includes_children(self):
        parent = self._make_folder('documents')
        child = self._make_folder('reports', parent=parent)
        url = reverse('nodes-view-set-detail', kwargs={'id': parent.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['children']), 1)
        self.assertEqual(response.data['children'][0]['id'], child.id)

    def test_retrieve_returns_parent_id(self):
        parent = self._make_folder('documents')
        child = self._make_folder('reports', parent=parent)
        url = reverse('nodes-view-set-detail', kwargs={'id': child.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['parent'], parent.id)

    def test_retrieve_root_node_has_null_parent(self):
        node = self._make_folder('documents')
        url = reverse('nodes-view-set-detail', kwargs={'id': node.id})
        response = self.client.get(url)
        self.assertIsNone(response.data['parent'])

    def test_retrieve_nonexistent_node_returns_404(self):
        url = reverse('nodes-view-set-detail', kwargs={'id': 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# DELETE /api/nodes/<id>/  — destroy
# ---------------------------------------------------------------------------

class NodesViewSetDestroyTests(BaseNodeTest):

    def test_destroy_leaf_node_returns_204(self):
        node = self._make_folder('documents')
        url = reverse('nodes-view-set-detail', kwargs={'id': node.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_destroy_removes_node_from_database(self):
        node = self._make_folder('documents')
        url = reverse('nodes-view-set-detail', kwargs={'id': node.id})
        self.client.delete(url)
        self.assertFalse(Node.objects.filter(id=node.id).exists())

    def test_destroy_nonempty_folder_without_confirm_returns_error(self):
        parent = self._make_folder('documents')
        self._make_folder('reports', parent=parent)
        url = reverse('nodes-view-set-detail', kwargs={'id': parent.id})
        response = self.client.delete(url)
        # APIException has status_code 500 by default
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('confirm', str(response.data['detail']))

    def test_destroy_nonempty_folder_without_confirm_does_not_delete(self):
        parent = self._make_folder('documents')
        self._make_folder('reports', parent=parent)
        url = reverse('nodes-view-set-detail', kwargs={'id': parent.id})
        self.client.delete(url)
        self.assertTrue(Node.objects.filter(id=parent.id).exists())

    def test_destroy_nonempty_folder_with_confirm_returns_204(self):
        parent = self._make_folder('documents')
        self._make_folder('reports', parent=parent)
        url = reverse('nodes-view-set-detail', kwargs={'id': parent.id})
        response = self.client.delete(f'{url}?confirm=true')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_destroy_nonempty_folder_with_confirm_cascades_to_children(self):
        parent = self._make_folder('documents')
        child = self._make_folder('reports', parent=parent)
        url = reverse('nodes-view-set-detail', kwargs={'id': parent.id})
        self.client.delete(f'{url}?confirm=true')
        self.assertFalse(Node.objects.filter(id=child.id).exists())

    def test_destroy_file_node_returns_204(self):
        node = self._make_file('readme.txt')
        url = reverse('nodes-view-set-detail', kwargs={'id': node.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_destroy_nonexistent_node_returns_404(self):
        url = reverse('nodes-view-set-detail', kwargs={'id': 99999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# GET /api/nodes/list/  — list (with optional parent / search filters)
# ---------------------------------------------------------------------------

class NodeListViewTests(BaseNodeTest):

    def setUp(self):
        super().setUp()
        self.url = reverse('node-list')

    def test_list_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_returns_all_nodes(self):
        self._make_folder('documents')
        self._make_folder('photos')
        self._make_file('readme.txt')
        response = self.client.get(self.url)
        self.assertEqual(response.data['count'], 3)

    def test_list_response_contains_expected_fields(self):
        self._make_folder('documents')
        response = self.client.get(self.url)
        item = response.data['results'][0]
        self.assertIn('id', item)
        self.assertIn('original_name', item)
        self.assertIn('type', item)
        self.assertIn('created_at', item)

    def test_list_filter_by_parent_returns_direct_children(self):
        parent = self._make_folder('documents')
        child1 = self._make_folder('reports', parent=parent)
        child2 = self._make_file('notes.txt', parent=parent)
        other = self._make_folder('photos')
        response = self.client.get(self.url, {'parent': parent.id})
        self.assertEqual(response.data['count'], 2)
        result_ids = {item['id'] for item in response.data['results']}
        self.assertIn(child1.id, result_ids)
        self.assertIn(child2.id, result_ids)
        self.assertNotIn(other.id, result_ids)

    def test_list_filter_by_search_matches_startswith(self):
        self._make_folder('documents')
        self._make_folder('downloads')
        self._make_folder('photos')
        response = self.client.get(self.url, {'search': 'doc'})
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['original_name'], 'documents')

    def test_list_filter_by_search_returns_multiple_matches(self):
        self._make_folder('documents')
        self._make_folder('downloads')
        self._make_folder('photos')
        response = self.client.get(self.url, {'search': 'do'})
        self.assertEqual(response.data['count'], 2)

    def test_list_filter_by_parent_and_search(self):
        parent = self._make_folder('root')
        self._make_folder('documents', parent=parent)
        self._make_folder('downloads', parent=parent)
        self._make_folder('photos', parent=parent)
        response = self.client.get(self.url, {'parent': parent.id, 'search': 'do'})
        self.assertEqual(response.data['count'], 2)

    def test_list_returns_empty_for_unknown_parent(self):
        self._make_folder('documents')
        response = self.client.get(self.url, {'parent': 99999})
        self.assertEqual(response.data['count'], 0)

    def test_list_returns_empty_when_search_has_no_match(self):
        self._make_folder('documents')
        response = self.client.get(self.url, {'search': 'xyz'})
        self.assertEqual(response.data['count'], 0)


# ---------------------------------------------------------------------------
# POST /api/nodes/bulk-delete/  — bulk delete
# ---------------------------------------------------------------------------

class BulkDeleteViewTests(BaseNodeTest):

    def setUp(self):
        super().setUp()
        self.url = reverse('node-bulk-delete')

    def test_bulk_delete_returns_207(self):
        node1 = self._make_folder('documents')
        node2 = self._make_folder('photos')
        response = self.client.post(self.url, {'ids': [node1.id, node2.id]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)

    def test_bulk_delete_removes_nodes_from_database(self):
        node1 = self._make_folder('documents')
        node2 = self._make_folder('photos')
        self.client.post(self.url, {'ids': [node1.id, node2.id]}, format='json')
        self.assertEqual(Node.objects.filter(id__in=[node1.id, node2.id]).count(), 0)

    def test_bulk_delete_cascades_children(self):
        parent = self._make_folder('documents')
        child = self._make_folder('reports', parent=parent)
        self.client.post(self.url, {'ids': [parent.id]}, format='json')
        self.assertFalse(Node.objects.filter(id=child.id).exists())

    def test_bulk_delete_does_not_affect_other_nodes(self):
        node1 = self._make_folder('documents')
        node2 = self._make_folder('photos')
        other = self._make_folder('videos')
        self.client.post(self.url, {'ids': [node1.id, node2.id]}, format='json')
        self.assertTrue(Node.objects.filter(id=other.id).exists())

    def test_bulk_delete_missing_ids_returns_400(self):
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_delete_empty_ids_returns_400(self):
        response = self.client.post(self.url, {'ids': []}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_delete_two_separate_trees_removes_both(self):
        tree1 = self._make_folder('tree1')
        tree1_child = self._make_folder('child1', parent=tree1)
        tree2 = self._make_folder('tree2')
        tree2_child = self._make_folder('child2', parent=tree2)
        self.client.post(self.url, {'ids': [tree1.id, tree2.id]}, format='json')
        surviving = Node.objects.filter(id__in=[tree1.id, tree1_child.id, tree2.id, tree2_child.id]).count()
        self.assertEqual(surviving, 0)