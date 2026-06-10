import os
import shutil

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from filesystem.models import Node, NodeTypes
from django.conf import settings

from filesystem.repositories import NodeRepository


@receiver(post_save, sender=Node)
def sync_filesystem_on_create(sender, instance: Node, **kwargs):
    created = kwargs['created']

    if not created:
        return

    path = _create_root_path_for_node(instance)

    if os.path.exists(path):
        return

    if instance.type == NodeTypes.FOLDER:
        os.mkdir(path)
        os.chmod(path, 0o755)

    if instance.type == NodeTypes.FILE:
        _touch(path)


@receiver(post_delete, sender=Node)
def sync_filesystem_on_delete(sender, instance: Node, **kwargs):
    path = f'{_create_root_path_for_node(instance)}{instance.original_name}'

    if path == settings.FILE_SYSTEM_ROOT+'/':
        # Protect from deleting root
        return

    if os.path.exists(path):
        shutil.rmtree(path) # Delete the entire structure. This will basically delete recursively (mimic sudo rm -r)

def _create_root_path_for_node(instance: Node)->str:
    root = settings.FILE_SYSTEM_ROOT
    node_chain = NodeRepository().find_node_parent_chain(node=instance)

    return f'{root}/{node_chain}'

def _touch(path):
    with open(path, 'a'):
        os.utime(path, None)

