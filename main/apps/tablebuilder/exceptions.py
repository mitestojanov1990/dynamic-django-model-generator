from rest_framework.serializers import ValidationError


class TableBuilderSerializerException(ValidationError):
    pass


class TableAlreadyExistsException(TableBuilderSerializerException):
    pass


class GenerateTableException(TableBuilderSerializerException):
    pass


class TableColumnAlreadyExistsException(TableBuilderSerializerException):
    pass
