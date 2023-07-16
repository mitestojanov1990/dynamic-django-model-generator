"""Helpers used across project tablebuilder"""
from importlib import reload
import sys
import uuid

from django.apps import apps
from django.db import connection, models

from main.apps.tablebuilder.constants import APP_NAME, TABLE_FIELD_DEFAULT_STRING_LENGTH


def _get_field_class(
    field_name,
    field_type,
):
    if field_type == "string":
        field_class = models.CharField(max_length=TABLE_FIELD_DEFAULT_STRING_LENGTH)
    elif field_type == "number":
        field_class = models.IntegerField()
    elif field_type == "boolean":
        field_class = models.BooleanField()
    elif field_name == "id":
        field_class = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    else:
        raise ValueError(f"Invalid field type: {field_type}")

    return field_class


def create_dynamic_model(name, columns=None, app_label="", module="", options=None):
    """
    Dynamically create a new model and its corresponding database table.
    """

    class Meta:
        # Using type('Meta', ...) gives a dictproxy error during model creation
        pass

    if app_label:
        # app_label must be set using the Meta inner class
        setattr(Meta, "app_label", app_label)

    if options is not None:
        for key, value in options.items():
            setattr(Meta, key, value)

    attrs = {"__module__": module, "Meta": Meta}

    if columns:
        if not any("id" in field for field in columns):
            id_field = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
            attrs["id"] = id_field
        for dic in columns:
            field_name = dic.get("name")
            field_type = dic.get("type")
            field_class = _get_field_class(field_name, field_type)

            attrs[field_name] = field_class

    model = type(name, (models.Model,), attrs)

    return model


def create_model_and_table(app_label, model_name, columns):
    model = create_dynamic_model(model_name, columns, app_label)

    # Register the model with Django's app registry
    apps.register_model(APP_NAME, model)
    apps.all_models[app_label][model_name.lower()] = model

    # Use the schema_editor to create the table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(model)


def add_field_to_model(model, field_name, field_type):
    """
    Adds a field to a model
    """

    field_class = _get_field_class(field_name, field_type)

    # Use Django's schema editor to add the field
    with connection.schema_editor() as schema_editor:
        field_class.set_attributes_from_name(field_name)
        field_class.model = model
        schema_editor.add_field(model, field_class)


def modify_model(model, old_field_name, field_name, field_type):
    """
    Modify a model using Django's SchemaEditor.
    """
    with connection.schema_editor() as schema_editor:
        field_class = _get_field_class(field_name, field_type)
        field_class.set_attributes_from_name(field_name)
        old_field = model._meta.get_field(old_field_name)
        schema_editor.alter_field(model, old_field, field_class)


def remove_fields_from_model(model, fields_to_remove):
    """
    Removes specified fields from a model
    """
    with connection.schema_editor() as schema_editor:
        for field_name in fields_to_remove:
            field = model._meta.get_field(field_name)
            schema_editor.remove_field(model, field)


def reload_app_models(app_name):
    """
    Reloads the models module of the specified app and resets the app cache.

    This is useful when schema changes have been applied to models at runtime.
    """
    # Reload the app's models module
    module = apps.get_app_config(app_name).name
    reload(sys.modules[module])

    # Reset the apps cache
    apps.all_models[app_name].clear()
    apps.clear_cache()
