from django.contrib.gis.geos import Point
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from .models import Category, Service


class BaseSetup(APITestCase):
    """Shared users + sample geo data for service/category tests."""

    def setUp(self):
        self.admin = User.objects.create_user(username="admin", password="x", role="ADMIN")
        self.staff = User.objects.create_user(username="staff", password="x", role="STAFF")
        self.user = User.objects.create_user(username="user", password="x", role="USER")

        self.hospital = Category.objects.create(name="Hospital")
        self.atm = Category.objects.create(name="ATM")

        # Reference point for nearby search: (lat=19.0, lng=73.0) -> Point(lng, lat)
        # near: ~0 km, mid: ~5 km away, far: well beyond a small radius.
        self.near = Service.objects.create(
            name="Near Hospital", category=self.hospital,
            location=Point(73.0, 19.0), rating=4.5, created_by=self.admin,
        )
        self.mid = Service.objects.create(
            name="Mid ATM", category=self.atm,
            location=Point(73.045, 19.0), rating=3.0, created_by=self.admin,  # ~4.7 km east
        )
        self.far = Service.objects.create(
            name="Far Hospital", category=self.hospital,
            location=Point(73.5, 19.0), rating=5.0, created_by=self.admin,  # ~52 km east
        )


class CategoryPermissionTests(BaseSetup):
    def test_list_requires_authentication(self):
        self.assertEqual(
            self.client.get("/api/services/categories/").status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_authenticated_user_can_list(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/services/categories/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_admin_can_create_category(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.post(
            "/api/services/categories/create/", {"name": "Shop"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Category.objects.filter(name="Shop").exists())

    def test_staff_cannot_create_category(self):
        self.client.force_authenticate(user=self.staff)
        res = self.client.post(
            "/api/services/categories/create/", {"name": "Shop"}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_category(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.delete(f"/api/services/categories/{self.atm.id}/delete/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)


class ServicePermissionTests(BaseSetup):
    def _create_payload(self):
        return {
            "name": "New Clinic",
            "category": self.hospital.id,
            "latitude": 19.01,
            "longitude": 73.01,
            "rating": 4.0,
        }

    def test_user_cannot_create_service(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post(
            "/api/services/services/create/", self._create_payload(), format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_create_service(self):
        self.client.force_authenticate(user=self.staff)
        res = self.client.post(
            "/api/services/services/create/", self._create_payload(), format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        created = Service.objects.get(name="New Clinic")
        # created_by should be the requesting staff user
        self.assertEqual(created.created_by, self.staff)
        # location built from latitude/longitude
        self.assertAlmostEqual(created.location.y, 19.01, places=4)
        self.assertAlmostEqual(created.location.x, 73.01, places=4)

    def test_staff_can_update_service(self):
        self.client.force_authenticate(user=self.staff)
        res = self.client.patch(
            f"/api/services/services/{self.near.id}/update/",
            {"name": "Renamed Hospital"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.near.refresh_from_db()
        self.assertEqual(self.near.name, "Renamed Hospital")

    def test_staff_cannot_delete_service(self):
        self.client.force_authenticate(user=self.staff)
        res = self.client.delete(f"/api/services/services/{self.near.id}/delete/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_service(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.delete(f"/api/services/services/{self.near.id}/delete/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Service.objects.filter(id=self.near.id).exists())

    def test_service_list_exposes_coordinates(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/services/services/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        sample = res.data[0]
        self.assertIn("latitude", sample)
        self.assertIn("longitude", sample)


class CategoryFilterTests(BaseSetup):
    def test_filter_services_by_category(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/services/services/?category=ATM")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        names = {s["name"] for s in res.data}
        self.assertEqual(names, {"Mid ATM"})


class NearbySearchTests(BaseSetup):
    BASE = "/api/services/services/nearby/?lat=19.0&lng=73.0"

    def test_requires_authentication(self):
        self.assertEqual(
            self.client.get(self.BASE).status_code, status.HTTP_401_UNAUTHORIZED
        )

    def test_returns_only_services_within_radius(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(self.BASE + "&radius=10")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        names = {r["name"] for r in res.data["results"]}
        # near + mid are within 10 km; far (~52 km) is excluded
        self.assertEqual(names, {"Near Hospital", "Mid ATM"})
        self.assertEqual(res.data["count"], 2)

    def test_results_sorted_by_distance_and_include_distance(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(self.BASE + "&radius=100")
        results = res.data["results"]
        distances = [r["distance_km"] for r in results]
        self.assertEqual(distances, sorted(distances))
        self.assertEqual(results[0]["name"], "Near Hospital")
        self.assertAlmostEqual(results[0]["distance_km"], 0.0, places=1)

    def test_nearby_category_filter(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(self.BASE + "&radius=100&category=Hospital")
        names = {r["name"] for r in res.data["results"]}
        self.assertEqual(names, {"Near Hospital", "Far Hospital"})

    def test_invalid_coordinates_return_400(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/services/services/nearby/?lat=abc&lng=73.0")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
