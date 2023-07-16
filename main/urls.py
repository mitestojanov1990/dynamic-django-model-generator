from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from main.apps.tablebuilder.helpers import generate_tables_on_startup, reload_app_models

urlpatterns = [
    path("", RedirectView.as_view(url="/api/")),
    path("admin/", admin.site.urls),
    path("api/", include("main.apps.tablebuilder.urls")),
]

# generate tables if any
generate_tables_on_startup()
