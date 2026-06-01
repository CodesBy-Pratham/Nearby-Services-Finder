from .models import Category, Service
from .serializers import CategorySerializer, ServiceSerializer
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsAdmin, IsStaffOrAdmin
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from rest_framework.response import Response
from rest_framework.views import APIView


class CategoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)


class CategoryCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class CategoryUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class CategoryDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=404)
        category.delete()
        return Response({"message": "Category deleted successfully"}, status=204)


class ServiceListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        services = Service.objects.select_related("category").all()

        category = request.query_params.get("category")
        if category:
            services = services.filter(category__name__iexact=category)

        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data)


class ServiceCreateView(APIView):
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    def post(self, request):
        serializer = ServiceSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class ServiceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            service = Service.objects.select_related("category").get(pk=pk)
        except Service.DoesNotExist:
            return Response({"error": "Service not found"}, status=404)
        serializer = ServiceSerializer(service)
        return Response(serializer.data)


class ServiceUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsStaffOrAdmin]

    def patch(self, request, pk):
        try:
            service = Service.objects.get(pk=pk)
        except Service.DoesNotExist:
            return Response({"error": "Service not found"}, status=404)
        serializer = ServiceSerializer(
            service, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class ServiceDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, pk):
        try:
            service = Service.objects.get(pk=pk)
        except Service.DoesNotExist:
            return Response({"error": "Service not found"}, status=404)
        service.delete()
        return Response({"message": "Service deleted successfully"}, status=204)


class NearbyServicesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            lat = float(request.query_params.get("lat"))
            lng = float(request.query_params.get("lng"))
            radius = float(request.query_params.get("radius", 5))
        except (TypeError, ValueError):
            return Response({"error": "Invalid lat/lng/radius"}, status=400)

        category = request.query_params.get("category")

        user_location = Point(lng, lat, srid=4326)

        queryset = Service.objects.select_related("category")

        # radius filter
        queryset = (
            queryset.filter(location__distance_lte=(user_location, D(km=radius)))
            .annotate(distance=Distance("location", user_location))
            .order_by("distance")
        )

        #  category filter (optional)
        if category:
            queryset = queryset.filter(category__name__iexact=category)

        results = []
        for service in queryset:
            results.append(
                {
                    "id": service.id,
                    "name": service.name,
                    "category": service.category.name,
                    "rating": service.rating,
                    "distance_km": round(service.distance.km, 2),
                    "latitude": service.location.y,
                    "longitude": service.location.x,
                }
            )

        return Response({"count": len(results), "results": results})
