from rest_framework.routers import DefaultRouter

from main.apps.tablebuilder.viewsets import TableBuilderViewSet


router = DefaultRouter()
router.register("table", TableBuilderViewSet, basename="")

urlpatterns = router.urls + []
