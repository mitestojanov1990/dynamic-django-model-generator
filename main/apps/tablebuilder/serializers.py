"""Serializers"""
from django.apps import apps
from django.db import IntegrityError, transaction
from rest_framework import serializers

from main.apps.tablebuilder.constants import (
    APP_NAME,
    TABLE_NAME_MAX_LENGTH,
    TABLE_FIELD_DEFAULT_STRING_LENGTH,
)
from main.apps.tablebuilder.exceptions import (
    TableAlreadyExistsException,
)
from main.apps.tablebuilder.helpers import (
    add_field_to_model,
    create_model_and_table,
    modify_model,
    remove_fields_from_model,
)
from main.apps.tablebuilder.models import TableStructure


class FieldDefinitionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=TABLE_FIELD_DEFAULT_STRING_LENGTH)
    old_name = serializers.CharField(max_length=TABLE_FIELD_DEFAULT_STRING_LENGTH, required=False)
    type = serializers.ChoiceField(choices=["string", "number", "boolean"])


class TableDefinitionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=TABLE_NAME_MAX_LENGTH, required=True)
    columns = FieldDefinitionSerializer(many=True, required=True)


class TableStructureSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=TABLE_FIELD_DEFAULT_STRING_LENGTH)

    class Meta:
        model = TableStructure
        fields = "__all__"

    @transaction.atomic
    def create(self, validated_data):
        name = validated_data.get("name")
        try:
            obj = super().create(validated_data)
            create_model_and_table(APP_NAME, name, validated_data.get("columns"))
            return obj
        except IntegrityError as exc:
            try:
                del apps.all_models[APP_NAME][name]
            except KeyError:
                pass
            raise TableAlreadyExistsException(f"Table `{name}` already exists.") from exc

    @transaction.atomic
    def update(self, instance, validated_data):
        name = validated_data.get("name")
        columns_serialized = FieldDefinitionSerializer(
            many=True, data=validated_data.get("columns")
        )
        columns_serialized.is_valid(raise_exception=True)
        columns = columns_serialized.validated_data

        validated_data.setdefault("columns", instance.columns)
        model = apps.get_model(APP_NAME, name, require_ready=False)

        # Get set of new field names
        new_field_names = set(column.get("name") for column in columns)

        # Get set of existing field names
        existing_field_names = set(
            field.name for field in model._meta.fields if field.name != "id"
        )  # Exclude the id field

        # Identify the fields that need to be removed
        fields_to_remove = existing_field_names - new_field_names

        # Identify the fields that need to be added
        fields_to_add = new_field_names - existing_field_names
        for column in columns:
            column_name = column.get("name")
            column_type = column.get("type")
            old_column_name = column.setdefault("old_name", None)

            # If field needs to be updated
            if column_name in existing_field_names and old_column_name != column_name:
                exists = [field for field in model._meta.fields if field.name == old_column_name]
                if len(exists) > 0:
                    modify_model(model, old_column_name, column_name, column_type)
                    validated_data["columns"] = [
                        column if col.get("name") == old_column_name else col
                        for col in validated_data.get("columns")
                        if col.get("name") == old_column_name
                    ]

            # If field needs to be added
            elif column_name in fields_to_add:
                add_field_to_model(model, column_name, column_type)

        # Remove fields
        remove_fields_from_model(model, fields_to_remove)

        return super().update(instance, validated_data)


def create_serializer(model):
    class_name = f"{model.__name__}Serializer"
    meta_class = type("Meta", (), {"model": model, "fields": "__all__"})
    serializer_class = type(class_name, (serializers.ModelSerializer,), {"Meta": meta_class})
    return serializer_class
