from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModelMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        abstract = True

class NodeTypes(models.TextChoices):
    FOLDER = 'FOLDER', _('Folder')
    FILE = 'FILE', _('File')

class Node(TimeStampedModelMixin, models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True, unique=True)
    original_name = models.CharField(max_length=255, db_index=True)
    type = models.CharField(choices=NodeTypes.choices, max_length=20, default=NodeTypes.FOLDER)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children', on_delete=models.CASCADE)

    def __str__(self):
        return f'Node {self.original_name} of type {self.type}'

    class Meta:
        db_table = 'nodes'
        verbose_name = 'Nodes'
        verbose_name_plural = 'Nodes'
