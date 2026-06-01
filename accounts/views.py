from rest_framework import generics
from .models import User
from .serializers import RegisterSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .permissions import IsAdmin

# Create your views here.


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "id": request.user.id,
                "username": request.user.username,
                "role": request.user.role,
            }
        )


class UserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        users = User.objects.all().order_by("username")
        return Response(
            [
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "role": u.role,
                }
                for u in users
            ]
        )


class AssignRoleView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        role = request.data.get("role")
        if role not in ["USER", "STAFF", "ADMIN"]:
            return Response(
                {"error": "Invalid role. Choose USER, STAFF or ADMIN"}, status=400
            )

        user.role = role
        user.save()
        return Response({"message": f"Role updated to {role} for {user.username}"})
