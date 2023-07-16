from uuid import uuid4 as uuid
from django.apps import apps
from django.db import transaction
from django.db.models import Q
from rest_framework import serializers

from main.apps.tablebuilder.constants import (
    APP_NAME,
    TABLE_NAME_MAX_LENGTH,
    TABLE_FIELD_DEFAULT_STRING_LENGTH,
)
from main.apps.tablebuilder.helpers import (
    add_field_to_model,
    register_dynamic_model,
    create_db_table,
    modify_model,
    remove_fields_from_model,
)
from main.apps.tablebuilder.models import FieldDefinition, TableStructure


class FieldDefinitionSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField()
    name = serializers.CharField(max_length=TABLE_FIELD_DEFAULT_STRING_LENGTH)
    old_name = serializers.CharField(max_length=TABLE_FIELD_DEFAULT_STRING_LENGTH, required=False)
    type = serializers.ChoiceField(choices=["string", "number", "boolean"])
    table_structure_id = serializers.UUIDField(required=False, write_only=True)

    class Meta:
        model = FieldDefinition
        fields = (
            "id",
            "name",
            "old_name",
            "type",
            "table_structure_id",
        )

    def to_internal_value(self, data):
        id = data.setdefault("id", uuid())
        return super().to_internal_value(data)


class FieldDefinitionReadOnlySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=TABLE_FIELD_DEFAULT_STRING_LENGTH)
    old_name = serializers.CharField(max_length=TABLE_FIELD_DEFAULT_STRING_LENGTH, required=False)
    type = serializers.ChoiceField(choices=["string", "number", "boolean"])


class TableDefinitionReadOnlySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=TABLE_NAME_MAX_LENGTH, required=True)
    field_definitions = FieldDefinitionSerializer(many=True, required=True)


class TableStructureSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=TABLE_FIELD_DEFAULT_STRING_LENGTH)
    field_definitions = FieldDefinitionSerializer(many=True)

    class Meta:
        model = TableStructure
        fields = "__all__"

    @transaction.atomic
    def create(self, validated_data):
        name = validated_data.get("name")
        field_definitions_data = []
        if "field_definitions" in validated_data:
            field_definitions_data = validated_data.pop("field_definitions", None)
        table_structure = TableStructure.objects.create(**validated_data)
        custom_updater(
            "table_structure_id",
            table_structure.id,
            table_structure.field_definitions,
            FieldDefinition,
            FieldDefinitionSerializer,
            field_definitions_data,
        )
        model = register_dynamic_model(
            APP_NAME, name, field_definitions_data, "main.apps.tablebuilder.models"
        )
        create_db_table(model)
        return table_structure

    @transaction.atomic
    def update(self, instance, validated_data):
        if validated_data.get("name"):
            instance.name = validated_data["name"]

        name = validated_data.get("name")

        field_definitions_data = []
        if "field_definitions" in validated_data:
            field_definitions_data = validated_data.pop("field_definitions")
            custom_updater(
                "table_structure_id",
                instance.id,
                instance.field_definitions,
                FieldDefinition,
                FieldDefinitionSerializer,
                field_definitions_data,
            )
        instance.save()
        model = apps.get_model(APP_NAME, name, require_ready=False)

        # Get set of new field names
        new_field_definitions = [field_definition for field_definition in field_definitions_data]

        # Get set of existing field names
        existing_field_definitions = [
            field for field in model._meta.fields if field.name != "id"
        ]  # Exclude the id field

        new_field_names = set(field.get("name") for field in new_field_definitions)
        existing_field_names = set(field.name for field in existing_field_definitions)
        field_names_to_update = set(
            field.get("old_name") for field in field_definitions_data if "old_name" in field
        )
        field_definitions_to_update = [
            field for field in field_definitions_data if "old_name" in field
        ]
        # Identify the fields that need to be removed
        field_names_to_remove = existing_field_names - new_field_names

        # Identify the fields that need to be added
        field_names_to_add = new_field_names - existing_field_names
        # for field_definition in fields_to_add:existing_field_names
        for field_name in field_names_to_add:
            field_definition = [
                field_def
                for field_def in field_definitions_data
                if field_def.get("name") == field_name
            ]
            if len(field_definition) < 1:
                continue
            field_definition = field_definition[0]
            add_field_to_model(model, field_name, field_definition.get("type"))

        for field_name in existing_field_names:
            field_definition = [
                field_def
                for field_def in field_definitions_to_update
                if field_def.get("old_name") == field_name
            ]
            if len(field_definition) < 1:
                continue
            field_definition = field_definition[0]

            column_name = field_definition.get("name")
            column_type = field_definition.get("type")
            old_column_name = field_definition.get("old_name")
            try:
                if not hasattr(model, field_name):
                    modify_model(model, old_column_name, column_name, column_type)
            except Exception as exc:
                print(exc)
                raise exc

        # Remove fields
        remove_fields_from_model(model, field_names_to_remove)

        return instance


def create_serializer1(model):
    class_name = f"{model.__name__}Serializer"
    meta_class = type("Meta", (), {"model": model, "fields": "__all__"})
    serializer_class = type(class_name, (serializers.ModelSerializer,), {"Meta": meta_class})
    return serializer_class


def create_serializer(model_name):
    # Get the model from all the Django app models
    MODEL = apps.get_model(APP_NAME, model_name)

    # Now we'll create a serializer dynamically
    class DynamicModelSerializer(serializers.ModelSerializer):
        class Meta:
            model = MODEL
            fields = "__all__"

    return DynamicModelSerializer


def delete_items(set_items, used_model, new_data):
    """Delete items.

    Iterare new_data and get all items that exist in the database, then
    filter set_items and delete all extra items.
    """
    ids = []
    for item in new_data:
        if item.get("id"):
            id = item.get("id")
            try:
                used_model.objects.get(pk=id)
                ids.append(id)
            except used_model.DoesNotExist:
                continue
    for item in set_items.all().filter(~Q(id__in=ids)):
        used_model.objects.get(pk=item.id).delete()


def custom_updater(
    parent_key,
    parent_id,
    set_items,
    used_model,
    used_serializer,
    data,
):
    items = []
    delete_items(set_items, used_model, data)
    for item in data:
        id = None
        if item.get("id"):
            id = item.get("id")

        try:
            filterset = Q(**{parent_key: parent_id})
            obj = used_model.objects.filter(filterset).get(pk=id)
            serialized = used_serializer(
                instance=obj,
                data=item,
            )

            serialized.is_valid(raise_exception=True)
            item_ = serialized.save()
            items.append(item_)
        except used_model.DoesNotExist:
            item["id"] = uuid()
            item.setdefault(parent_key, parent_id)
            serialized = used_serializer(data=item)
            serialized.is_valid(raise_exception=True)

            item_ = serialized.save()

            items.append(item_)
    return items
