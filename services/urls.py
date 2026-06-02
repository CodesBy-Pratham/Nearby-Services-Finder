from django.urls import path

from .views import (
    CategoryListView,
    CategoryCreateView,
    CategoryUpdateView,
    CategoryDeleteView,
    ServiceListView,
    ServiceCreateView,
    ServiceDetailView,
    ServiceUpdateView,
    ServiceDeleteView,
    NearbyServicesView,
)

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("categories/create/", CategoryCreateView.as_view(), name="category-create"),
    path(
        "categories/<int:pk>/update/",
        CategoryUpdateView.as_view(),
        name="category-update",
    ),
    path(
        "categories/<int:pk>/delete/",
        CategoryDeleteView.as_view(),
        name="category-delete",
    ),
    path("services/", ServiceListView.as_view(), name="service-list"),
    path("services/create/", ServiceCreateView.as_view(), name="service-create"),
    path("services/nearby/", NearbyServicesView.as_view(), name="nearby-services"),
    path("services/<int:pk>/", ServiceDetailView.as_view(), name="service-detail"),
    path(
        "services/<int:pk>/update/", ServiceUpdateView.as_view(), name="service-update"
    ),
    path(
        "services/<int:pk>/delete/", ServiceDeleteView.as_view(), name="service-delete"
    ),
]
