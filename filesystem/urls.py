from django.urls import path, include
from rest_framework import routers

from filesystem import views

nodes_router = routers.DefaultRouter()
nodes_router.register(r"nodes", views.NodesViewSet, basename="node-view-set")

urlpatterns = [
    path(
        "nodes/",
        views.NodesViewSet.as_view(
            {
                "post": "create",
            }
        ),
        name="nodes-view-set-create",
    ),
    path(
        'nodes/<int:id>/',
         views.NodesViewSet.as_view(
             {
                 "get": "retrieve",
                 "delete": "destroy"
             }
         ),
        name="nodes-view-set-detail",
    ),
    path('nodes/list/', views.NodeListView.as_view(), name="node-list"),
    path('nodes/bulk-delete/', views.BulkDeleteView.as_view(), name="node-bulk-delete"),
]