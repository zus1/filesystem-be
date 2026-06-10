from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer, OpenApiParameter
from rest_framework import serializers

from filesystem.serializers import NodeCreateSerializer, NodeSerializer

NODE_VIEW_SET = {
    "create": extend_schema(
        request=NodeCreateSerializer,
        responses={
            200: NodeSerializer,
            400: OpenApiResponse(
                description="Validation error",
                response=inline_serializer(
                    name="CreateNodeVAlidationErrorResponse",
                    fields={
                        "non_field_errors": serializers.ListField(),
                    },
                ),
            ),
        },
    ),
    "retrieve": extend_schema(
        parameters=[
            OpenApiParameter(
                name="id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH
            )
        ],
        description="The retrieve action returns a single object selected by `id`."
    )
}

NODE_LIST_VIEW = {
    "parameters": [
        OpenApiParameter(
            name="parent",
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.INT,
            required=False,
        ),
        OpenApiParameter(
            name="search",
            location=OpenApiParameter.QUERY,
            type=OpenApiTypes.STR,
            required=False,
        ),
    ],
}

BULK_DELETE_VIEW = {
    "request": inline_serializer(
        name="BulkDeleteNodesRequest",
        fields={
            "ids": serializers.ListField(),
        },
    ),
    "responses": {
        207: None,
    },
}