import uuid

from django.db import models
from django_extensions.db.models import TimeStampedModel

from main.apps.tablebuilder.constants import (
    TABLE_NAME_MAX_LENGTH,
)


class FieldDefinition(TimeStampedModel):
    """"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=TABLE_NAME_MAX_LENGTH)
    old_name = models.CharField(max_length=TABLE_NAME_MAX_LENGTH, null=True, default=None)
    type = models.CharField(max_length=50)
    table_structure = models.ForeignKey(
        "TableStructure", on_delete=models.CASCADE, related_name="field_definitions"
    )


class TableStructure(TimeStampedModel):
    """Model for storing table structures.

    TableStructures are populated by the user. They store the table name and are related to field definitions.
    TableStructures are used to generate Django Models on the fly.
    TableStructures are used as a reference for the actual dynamically generated tables.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=TABLE_NAME_MAX_LENGTH, unique=True)
