"""REST"""
from django.apps import apps
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from main.apps.tablebuilder.constants import APP_NAME
from main.apps.tablebuilder.models import TableStructure
from main.apps.tablebuilder.serializers import (
    TableDefinitionSerializer,
    TableStructureSerializer,
    create_serializer,
)


class TableBuilderViewSet(viewsets.ModelViewSet):
    """Endpoints"""

    queryset = TableStructure.objects.all()
    serializer_class = TableStructureSerializer

    def create(self, request: Request) -> Response:
        """"""
        definition_serializer = TableDefinitionSerializer(data=request.data)
        definition_serializer.is_valid(raise_exception=True)

        model_serializer = TableStructureSerializer(data=request.data)
        model_serializer.is_valid(raise_exception=True)
        model = model_serializer.save()

        return Response(status=status.HTTP_200_OK, data=model.pk)

    def update(self, request: Request, pk=None) -> Response:
        """Put"""
        definition_serializer = TableDefinitionSerializer(data=request.data)
        definition_serializer.is_valid(raise_exception=True)

        model_serializer = TableStructureSerializer(instance=self.get_object(), data=request.data)
        model_serializer.is_valid(raise_exception=True)
        model = model_serializer.save()

        return Response(status=status.HTTP_200_OK, data=pk)

    @action(methods=["post"], detail=True)
    def row(self, request: Request, pk=None) -> Response:
        obj = self.get_object()
        model = apps.get_model(APP_NAME, obj.name)
        s = create_serializer(model)(data=request.data)
        s.is_valid(raise_exception=True)
        saved_data = s.save()
        return Response(status=status.HTTP_200_OK, data=saved_data.pk)

    @action(methods=["get"], detail=True)
    def rows(self, request: Request, pk=None) -> Response:
        obj = self.get_object()
        model = apps.get_model(APP_NAME, obj.name)
        serializer_class = create_serializer(model)
        serializer = serializer_class(model.objects.all(), many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
