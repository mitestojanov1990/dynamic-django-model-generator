import uuid

from django.db.models import JSONField
from django.db import models
from django_extensions.db.models import TimeStampedModel

from main.apps.tablebuilder.constants import (
    TABLE_NAME_MAX_LENGTH,
)


class TableStructure(TimeStampedModel):
    """Model for storing table structures.

    TableStructures are populated by the user. They store the table name and
    JSON representing all the columns for the table and their definition.
    TableStructures are used to generate Django Models on the fly.
    TableStructures are used as a reference for the actual dynamically generated tables.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=TABLE_NAME_MAX_LENGTH, unique=True)
    columns = JSONField()
