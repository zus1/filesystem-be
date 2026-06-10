from django_mysql.models import QuerySet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import viewsets, generics
from rest_framework.decorators import action
from rest_framework.exceptions import APIException
from rest_framework.permissions import AllowAny

from filesystem.models import Node, NodeTypes
from filesystem.serializers import NodeCreateSerializer, NodeSerializer, NodeListSerializer


@extend_schema_view(
    create=extend_schema(
        request=NodeCreateSerializer,
        responses={200: NodeCreateSerializer, 400: str},
    ),
    retrieve=extend_schema(
        parameters=[OpenApiParameter(
            name="pk",
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
        )],
        description="The retrieve action returns a single object selected by `id`."
    )
)
class NodesViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.action == 'create':
            return NodeCreateSerializer
        if self.action == 'retrieve':
            return NodeSerializer

        return None

    def get_queryset(self)->QuerySet:
        return Node.objects.filter(id=self.kwargs['pk'])

    @action(detail=False, methods=['post'])
    def perform_create(self, serializer):
        serializer.save()

    @action(detail=True, methods=['delete'])
    def perform_destroy(self, instance: Node):
        confirm = self.request.query_params.get('confirm') == 'true'

        if instance.type == NodeTypes.FOLDER and instance.children.exists() and not confirm:
            raise APIException(detail='You are about to delete not empty folder, please confirm.')

        instance.delete()


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

