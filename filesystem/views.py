from django.http import JsonResponse
from django_mysql.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, inline_serializer, \
    OpenApiResponse
from rest_framework import viewsets, generics, status, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from filesystem.models import Node, NodeTypes
from filesystem.serializers import NodeCreateSerializer, NodeSerializer, NodeListSerializer
from filesystem import docs


@extend_schema_view(**docs.NODE_VIEW_SET)
class NodesViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    lookup_field = 'id'

    def get_serializer_class(self):
        if self.action == 'create':
            return NodeCreateSerializer
        if self.action == 'retrieve':
            return NodeSerializer

        return None

    def get_queryset(self)->QuerySet:
        return Node.objects.filter(id=self.kwargs[self.lookup_field])


    @action(detail=False, methods=['post'])
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        response_serializer = NodeSerializer(instance=serializer.instance)

        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'])
    def perform_destroy(self, instance: Node):
        confirm = self.request.query_params.get('confirm') == 'true'

        if instance.type == NodeTypes.FOLDER and instance.children.exists() and not confirm:
            raise APIException(detail='You are about to delete not empty folder, please confirm.')

        instance.delete()


@extend_schema(**docs.NODE_LIST_VIEW)
class NodeListView(generics.ListAPIView):
    model = Node
    permission_classes = (AllowAny,)
    serializer_class = NodeListSerializer

    def get_queryset(self)-> QuerySet:
        parent = self.request.query_params.get('parent', None)
        search = self.request.query_params.get('search', None)

        qs = Node.objects

        if parent:
            qs = qs.filter(parent=parent)
        if search:
            qs = qs.filter(original_name__startswith=search)

        return qs.all()

class BulkDeleteView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(**docs.BULK_DELETE_VIEW)
    def post(self, request)->JsonResponse:
        ids = request.data.get('ids', None)

        if not ids:
            raise APIException(detail='You have to provide some ids.', code=status.HTTP_400_BAD_REQUEST)

        Node.objects.filter(id__in=ids).delete()

        return JsonResponse({}, status=status.HTTP_207_MULTI_STATUS)

