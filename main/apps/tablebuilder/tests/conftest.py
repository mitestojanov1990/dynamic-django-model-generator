import pytest
from rest_framework.test import APIClient

from main.apps.tablebuilder.factories import TableStructureFactory
from main.apps.tablebuilder.models import FieldDefinition, TableStructure


# configure the APIClient
@pytest.fixture
def api_client():
    client = APIClient()
    return client


@pytest.fixture()
def users_table_data():
    TableStructure.objects.all().delete()
    return {
        "name": "users",
        "field_definitions": [
            {"name": "first_name", "type": "string"},
            {"name": "last_name", "type": "string"},
            {"name": "phone_number", "type": "number"},
            {"name": "subscriber", "type": "boolean"},
        ],
    }


@pytest.fixture()
def users_table_update_data():
    return {
        "name": "users",
        "field_definitions": [
            {"name": "email", "type": "string"},
            {"name": "address", "type": "string"},
            {"name": "phone_number", "type": "number", "old_name": "phone_number"},
            {"name": "registered", "type": "boolean", "old_name": "subscriber"},
        ],
    }


@pytest.fixture()
def invalid_type_users_table_data():
    TableStructure.objects.all().delete()
    return {
        "name": "users",
        "field_definitions": [
            {"name": "first_name", "type": "string"},
            {"name": "last_name", "type": "string"},
            {"name": "phone_number", "type": "integer"},
            {"name": "subscriber", "type": "boolean"},
        ],
    }


@pytest.fixture()
def user_logins_table():
    return {
        "name": "user_logins",
        "field_definitions": [
            {"name": "user_id", "type": "number"},
            {"name": "is_loggedin_", "type": "boolean"},
        ],
    }


@pytest.fixture()
def populated_tablebuilder_db():
    table_structure1 = TableStructureFactory.create(
        name="users",
    )

    first_name = create_new_field_definition("first_name", "string", None, table_structure1)
    last_name = create_new_field_definition("last_name", "string", None, table_structure1)
    phone_number = create_new_field_definition("phone_number", "number", None, table_structure1)
    subscriber = create_new_field_definition("subscriber", "boolean", None, table_structure1)

    table_structure2 = TableStructureFactory.create(
        name="user_logins",
    )
    is_logged_in = create_new_field_definition("is_logged_in", "boolean", None, table_structure2)
    return [table_structure1, table_structure2]


def create_new_field_definition(name, type, old_name, table_structure):
    return FieldDefinition.objects.create(
        name=name, type=type, old_name=old_name, table_structure=table_structure
    )
