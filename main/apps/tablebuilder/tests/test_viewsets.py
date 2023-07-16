import pytest
from django.apps import apps
from rest_framework import status

from main.apps.tablebuilder.constants import APP_NAME, TABLE_ALREADY_EXISTS_EXCEPTION_MESSAGE
from main.apps.tablebuilder.helpers import generate_tables_on_startup, reload_app_models
from main.apps.tablebuilder.models import TableStructure

pytestmark = pytest.mark.django_db


API_URL = "/api/table/"


def test_create(api_client, users_table_data):
    # Arrange
    url = API_URL
    name = users_table_data.get("name")
    # Act
    response = api_client.post(url, users_table_data, format="json")
    # Assert
    assert response.status_code == status.HTTP_200_OK
    model = apps.get_model(APP_NAME, name)
    assert model.__name__ == name

    # Ensure the response contains the primary key of the created object
    created_object = TableStructure.objects.get(pk=response.data)
    assert created_object is not None


def test_create_with_invalid_field_type(api_client, invalid_type_users_table_data):
    # Arrange
    url = API_URL
    # Act
    response = api_client.post(url, invalid_type_users_table_data, format="json")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    for column in response.data["field_definitions"]:
        error_type = column.setdefault("type", None)
        if error_type is None:
            continue
        assert "Is Not A Valid Choice." in error_type[0].title()


def test_create_with_existing_table_name(api_client, users_table_data):
    # Arrange
    url = API_URL
    name = users_table_data.get("name")
    same_name_data = {
        "name": name,
        "field_definitions": [
            {"name": "address", "type": "string"},
        ],
    }
    api_client.post(url, users_table_data, format="json")

    # Act
    response = api_client.post(url, same_name_data, format="json")
    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert f"`{name.capitalize()}` {TABLE_ALREADY_EXISTS_EXCEPTION_MESSAGE}" in str(
        response.data[0].title()
    )


def test_add_row(api_client, populated_tablebuilder_db):
    reload_app_models()
    generate_tables_on_startup()
    # Arrange
    obj = TableStructure.objects.get(name="users")
    id = obj.id
    name = obj.name
    # Data to post
    row_data = {
        "first_name": "Mite",
        "last_name": "Stojanov",
        "phone_number": 12345678,
        "subscriber": True,
    }
    url = f"{API_URL}{id}/row/"
    # Act
    response = api_client.post(url, row_data, format="json")

    # Assert
    assert response.status_code == status.HTTP_200_OK

    # Check if the posted data was saved correctly
    model = apps.get_model(APP_NAME, name)
    saved_instance = model.objects.first()

    assert response.data == saved_instance.id
    assert saved_instance.first_name == row_data["first_name"]
    assert saved_instance.last_name == row_data["last_name"]
    assert saved_instance.phone_number == row_data["phone_number"]
    assert saved_instance.subscriber == row_data["subscriber"]


def test_get(api_client, populated_tablebuilder_db):
    reload_app_models()
    generate_tables_on_startup()
    # Arrange
    obj = TableStructure.objects.get(name="users")
    id = obj.id
    name = obj.name
    # Data to post
    row_data = {
        "first_name": "Mite",
        "last_name": "Stojanov",
        "phone_number": 12345678,
        "subscriber": True,
    }
    url = f"{API_URL}{id}/row/"
    # add some data
    response = api_client.post(url, row_data, format="json")
    assert response.status_code == status.HTTP_200_OK
    # Create the URL for the get request
    url = f"{API_URL}{id}/rows/"
    # Act
    response = api_client.get(url)
    # Assert
    assert response.status_code == status.HTTP_200_OK
    model = apps.get_model(APP_NAME, name)
    assert (
        response.data[0]["first_name"]
        == model.objects.get(pk=response.data[0].get("id")).first_name
    )


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_generate_tables(populated_tablebuilder_db):
    reload_app_models()
    generate_tables_on_startup()
    try:
        model = apps.get_model(APP_NAME, "users")
    except Exception as exc:
        raise exc

    assert model.__name__ == "users"
