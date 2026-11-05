from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.scans.views import ScanViewSet
from apps.targets.views import TargetViewSet
from apps.vulnerabilities.views import VulnerabilityViewSet

router = DefaultRouter()
router.register(r"targets", TargetViewSet, basename="target")
router.register(r"scans", ScanViewSet, basename="scan")
router.register(r"vulnerabilities", VulnerabilityViewSet, basename="vulnerability")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include(router.urls)),
]
