"""REST"""
from django.apps import apps
from django.db import IntegrityError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from main.apps.tablebuilder.constants import APP_NAME, TABLE_ALREADY_EXISTS_EXCEPTION_MESSAGE
from main.apps.tablebuilder.exceptions import TableAlreadyExistsException
from main.apps.tablebuilder.models import TableStructure
from main.apps.tablebuilder.serializers import (
    TableDefinitionReadOnlySerializer,
    TableStructureSerializer,
    create_serializer,
)


class TableBuilderViewSet(viewsets.ModelViewSet):
    """Endpoints"""

    queryset = TableStructure.objects.all()
    serializer_class = TableStructureSerializer

    def create(self, request: Request) -> Response:
        """"""
        name = request.data.setdefault("name", None)
        definition_serializer = TableDefinitionReadOnlySerializer(data=request.data)
        definition_serializer.is_valid(raise_exception=True)

        model_serializer = TableStructureSerializer(data=request.data)
        model_serializer.is_valid(raise_exception=True)
        try:
            model = model_serializer.save()
        except IntegrityError as exc:
            if (
                len(
                    [
                        arg
                        for arg in exc.args
                        if "duplicate key value violates unique constraint" in arg
                    ]
                )
                > 0
            ):
                raise TableAlreadyExistsException(
                    f"`{name}` {TABLE_ALREADY_EXISTS_EXCEPTION_MESSAGE}"
                ) from exc
            raise exc

        return Response(status=status.HTTP_200_OK, data=model.pk)

    def update(self, request: Request, pk=None) -> Response:
        """Put"""
        definition_serializer = TableDefinitionReadOnlySerializer(data=request.data)
        definition_serializer.is_valid(raise_exception=True)

        model_serializer = TableStructureSerializer(instance=self.get_object(), data=request.data)
        model_serializer.is_valid(raise_exception=True)
        model = model_serializer.save()

        return Response(status=status.HTTP_200_OK, data=pk)

    @action(methods=["post"], detail=True)
    def row(self, request: Request, pk=None) -> Response:
        obj = self.get_object()
        # model = apps.get_model(APP_NAME, obj.name)
        s = create_serializer(obj.name)(data=request.data)
        s.is_valid(raise_exception=True)
        saved_data = s.save()
        return Response(status=status.HTTP_200_OK, data=saved_data.pk)

    @action(methods=["get"], detail=True)
    def rows(self, request: Request, pk=None) -> Response:
        obj = self.get_object()
        model = apps.get_model(APP_NAME, obj.name)
        serialized = create_serializer(obj.name)(model.objects.all(), many=True)

        return Response(serialized.data, status=status.HTTP_200_OK)
