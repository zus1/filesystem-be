import random

from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import NotFound

from filesystem.models import Node, NodeTypes


class ChildNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        exclude = ('updated_at', 'parent')

class NodeSerializer(serializers.ModelSerializer):
    children = ChildNodeSerializer(many=True)
    parent = serializers.SerializerMethodField()

    def get_parent(self, obj: Node)->int|None:
        return obj.parent.id if getattr(obj, 'parent', None) else None

    class Meta:
        model = Node
        exclude = ('updated_at',)

class NodeCreateSerializer(serializers.ModelSerializer):
    parent = serializers.IntegerField(required=False, allow_null=True, min_value=1)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__parent = None

    def validate(self, data):
        parent_id = data['parent']
        original_name = data['original_name']

        # First perform validation of this is a root node, aka no parent
        if not parent_id:
            if Node.objects.filter(parent__isnull=True, original_name=original_name).exists():
                raise serializers.ValidationError(f'Node with name {original_name} already exists in root directory')

            return super().validate(data)

        # Now perform validation if this is not a root node
        parent = Node.objects.filter(id=parent_id).first()
        if not parent:
            raise NotFound(f'Node with id {parent_id} does not exist')

        if Node.objects.filter(parent=parent, original_name=original_name).exists():
            raise serializers.ValidationError(f'Node with name {original_name} already exists in {parent.original_name} directory')

        # If parent found, set it and use it when creating object, else it stays None
        self.__parent = parent

        return super().validate(data)

    def create(self, data):
        name = f'{random.randint(1000000,9999999)}_{int(timezone.now().timestamp())}' \
            if data['type'] == NodeTypes.FILE.value else None

        data.pop('parent') # Remove parent id before setting values on model

        node = Node(**data)
        node.parent = self.__parent
        node.name = name
        node.save()

        return node

    class Meta:
        model = Node
        exclude = ('id', 'created_at', 'updated_at', 'name')

class NodeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ('id', 'created_at', 'original_name', 'type')