from rest_framework import serializers
from .models import Category, Service
from django.contrib.gis.geos import Point


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"


class ServiceSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)

    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Service

        fields = [
            "id",
            "name",
            "category",
            "category_name",
            "latitude",
            "longitude",
            "rating",
            "created_at",
        ]

        read_only_fields = ["created_at"]

    def create(self, validated_data):
        latitude = validated_data.pop("latitude")
        longitude = validated_data.pop("longitude")

        validated_data["location"] = Point(longitude, latitude)

        validated_data["created_by"] = self.context["request"].user

        return Service.objects.create(**validated_data)

    def update(self, instance, validated_data):
        latitude = validated_data.pop("latitude", None)
        longitude = validated_data.pop("longitude", None)

        if latitude is not None and longitude is not None:
            instance.location = Point(longitude, latitude)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.location:
            rep["latitude"] = instance.location.y
            rep["longitude"] = instance.location.x
        return rep
