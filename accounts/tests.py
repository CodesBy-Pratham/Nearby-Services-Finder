from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class RegistrationTests(APITestCase):
    def test_register_creates_user_with_default_role(self):
        res = self.client.post(
            "/api/auth/register/",
            {"username": "alice", "email": "alice@example.com", "password": "strongpass123"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="alice")
        self.assertEqual(user.role, "USER")
        # password must be hashed, not stored in plain text
        self.assertTrue(user.check_password("strongpass123"))

    def test_register_cannot_set_privileged_role(self):
        # role is not a registration field, so it is ignored even if supplied
        res = self.client.post(
            "/api/auth/register/",
            {
                "username": "mallory",
                "email": "m@example.com",
                "password": "strongpass123",
                "role": "ADMIN",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.get(username="mallory").role, "USER")


class LoginTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="bob", password="strongpass123")

    def test_login_returns_jwt_tokens(self):
        res = self.client.post(
            "/api/auth/",
            {"username": "bob", "password": "strongpass123"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_login_with_wrong_password_fails(self):
        res = self.client.post(
            "/api/auth/",
            {"username": "bob", "password": "wrong"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="carol", password="strongpass123")

    def test_profile_requires_authentication(self):
        res = self.client.get("/api/auth/profile/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_returns_current_user(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/auth/profile/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["username"], "carol")
        self.assertEqual(res.data["role"], "USER")


class UserManagementTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="admin", password="x", role="ADMIN")
        self.staff = User.objects.create_user(username="staff", password="x", role="STAFF")
        self.user = User.objects.create_user(username="user", password="x", role="USER")

    def test_admin_can_list_users(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.get("/api/auth/users/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        usernames = {u["username"] for u in res.data}
        self.assertEqual(usernames, {"admin", "staff", "user"})

    def test_non_admin_cannot_list_users(self):
        self.client.force_authenticate(user=self.staff)
        res = self.client.get("/api/auth/users/")
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_assign_role(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(
            f"/api/auth/users/{self.user.id}/assign-role/",
            {"role": "STAFF"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, "STAFF")

    def test_non_admin_cannot_assign_role(self):
        self.client.force_authenticate(user=self.staff)
        res = self.client.patch(
            f"/api/auth/users/{self.user.id}/assign-role/",
            {"role": "ADMIN"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_assign_invalid_role_rejected(self):
        self.client.force_authenticate(user=self.admin)
        res = self.client.patch(
            f"/api/auth/users/{self.user.id}/assign-role/",
            {"role": "SUPERHERO"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
