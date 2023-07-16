import factory
from factory.fuzzy import FuzzyText, FuzzyInteger
from factory.django import DjangoModelFactory

from main.apps.tablebuilder.helpers import sequence

from .models import TableStructure, FieldDefinition


class TableStructureFactory(DjangoModelFactory):
    """Db Table"""

    name = FuzzyText()

    class Meta:
        model = TableStructure


class FieldDefinitionFactory(DjangoModelFactory):
    """Db Table"""

    type = FuzzyText()
    name = FuzzyText()
    table_structure = factory.SubFactory(TableStructureFactory)

    class Meta:
        model = FieldDefinition


class DbJobProcessFactory(DjangoModelFactory):
    """Db Table"""

    type = FuzzyText()
    name = FuzzyText()
    status = FuzzyInteger(0, 1)
