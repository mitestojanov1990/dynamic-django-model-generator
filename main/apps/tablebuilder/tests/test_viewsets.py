import pytest
from django.apps import apps
from rest_framework.test import APIClient
from rest_framework import status

from main.apps.tablebuilder.constants import APP_NAME
from main.apps.tablebuilder.models import TableStructure
from main.apps.tablebuilder.serializers import (
    TableDefinitionSerializer,
    TableStructureSerializer,
    create_serializer,
)


# configure the APIClient
@pytest.fixture
def api_client():
    client = APIClient()
    return client


@pytest.mark.django_db
def test_create(api_client):
    # Arrange
    url = "/api/table/"
    data = {
        "name": "stuff",
        "columns": [
            {"name": "name", "type": "string", "old_name": 0},
            {"name": "address", "type": "string"},
            {"name": "number", "type": "number"},
            {"name": "subscriber", "type": "boolean"},
        ],
    }

    # Act
    response = api_client.post(url, data, format="json")
    # Assert
    assert response.status_code == status.HTTP_200_OK

    model = apps.get_model(APP_NAME, "stuff")
    assert model.__name__ == "stuff"

    # Ensure the response contains the primary key of the created object
    created_object = TableStructure.objects.get(pk=response.data)
    assert created_object is not None

    # Check if serializers work as expected
    definition_serializer = TableDefinitionSerializer(data=data)
    assert definition_serializer.is_valid()

    model_serializer = TableStructureSerializer(data=data)
    assert model_serializer.is_valid()

    # Check if a new object is indeed created
    assert TableStructure.objects.count() == 1


@pytest.mark.django_db
def test_create_with_invalid_field_type(api_client):
    # Arrange
    url = "/api/table/"
    data = {
        "name": "stuff",
        "columns": [
            {"name": "name", "type": "string", "old_name": 0},
            {"name": "address", "type": "invalid_field_type"},
        ],
    }
    # Act
    response = api_client.post(url, data, format="json")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Is Not A Valid Choice" in str(response.data["columns"][1]["type"][0].title())


@pytest.mark.django_db
def test_create_with_existing_table_name(api_client):
    table_name = "stuff"
    # Arrange
    url = "/api/table/"
    data1 = {
        "name": table_name,
        "columns": [
            {"name": "name", "type": "string", "old_name": 0},
        ],
    }
    data2 = {
        "name": table_name,
        "columns": [
            {"name": "address", "type": "string"},
        ],
    }
    api_client.post(url, data1, format="json")

    # Act
    response = api_client.post(url, data2, format="json")

    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert f"Table `{table_name.capitalize()}` Already Exists." in str(response.data[0].title())


@pytest.mark.django_db
def test_add_row(api_client):
    # Arrange
    # Create a dynamic model first
    table_data = {
        "name": "stuff",
        "columns": [
            {"name": "name", "type": "string", "old_name": 0},
            {"name": "address", "type": "string"},
        ],
    }
    table_create_url = "/api/table/"
    table_create_response = api_client.post(table_create_url, table_data, format="json")
    created_table_id = table_create_response.data

    # Data to post
    row_data = {"name": "Test", "address": "dummy address"}
    url = f"/api/table/{created_table_id}/row/"
    # Act
    response = api_client.post(url, row_data, format="json")

    # Assert
    assert response.status_code == status.HTTP_200_OK

    # Check if the posted data was saved correctly
    model = apps.get_model(APP_NAME, table_data["name"])
    saved_instance = model.objects.first()

    assert response.data == saved_instance.id
    assert saved_instance.name == row_data["name"]
    assert saved_instance.address == row_data["address"]


@pytest.mark.django_db
def test_get(api_client):
    table_name = "stuff"
    # Arrange
    url = "/api/table/"
    data = {
        "name": table_name,
        "columns": [
            {"name": "name", "type": "string", "old_name": 0},
            {"name": "address", "type": "string"},
            {"name": "number", "type": "number"},
            {"name": "subscriber", "type": "boolean"},
        ],
    }

    # Act
    response = api_client.post(url, data, format="json")
    # Create the URL for the get request
    url = f"/api/table/{response.data}/rows/"

    # Act
    response = api_client.get(url)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    model = apps.get_model(APP_NAME, table_name)
    # Ensure the response contains the data from your dynamic model instance
    serializer = create_serializer(model)(model.objects.all(), many=True)
    expected_data = serializer.data
    assert response.data == expected_data
