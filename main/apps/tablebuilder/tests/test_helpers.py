import pytest
from django.apps import apps
from main.apps.tablebuilder.constants import APP_NAME

from main.apps.tablebuilder.helpers import create_dynamic_model


# test that model is created correctly
@pytest.mark.django_db
def test_create_model():
    # arrange
    name = "TestModel"
    columns = [
        {"name": "field1", "type": "string"},
        {"name": "field2", "type": "number"},
        {"name": "field3", "type": "boolean"},
    ]
    app_label = APP_NAME
    module = "your_module_path"

    # act
    model = create_create_dynamic_modelmodel(name, columns, app_label, module)

    # assert
    # check that model was created correctly
    assert model.__name__ == name
    assert model._meta.app_label == app_label

    # check that columns were created correctly
    fields = model._meta.get_fields()
    assert len(fields) == len(columns) + 1  # +1 for the auto-created id field
    for column in columns:
        field = model._meta.get_field(column["name"])
        assert field is not None


# test that the created model can be fetched using get_model
@pytest.mark.django_db
def test_get_model():
    # arrange
    name = "TestModel2"
    columns = [
        {"name": "field1", "type": "string"},
        {"name": "field2", "type": "number"},
        {"name": "field3", "type": "boolean"},
    ]
    app_label = APP_NAME
    module = "your_module_path"

    # act
    model = create_dynamic_model(name, columns, app_label, module)

    # assert
    fetched_model = apps.get_model(app_label, name)
    assert fetched_model is not None
    assert fetched_model.__name__ == name
