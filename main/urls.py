from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/api/")),
    path("admin/", admin.site.urls),
    path("api/", include("main.apps.tablebuilder.urls")),
]
