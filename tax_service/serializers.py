from rest_framework import serializers
from .models import Order, ImportJob


class OrderCreateSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lon = serializers.FloatField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2)
    timestamp = serializers.DateTimeField(required=False)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = "__all__"


class ImportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImportJob
        fields = "__all__"


class ImportJobCreateSerializer(serializers.Serializer):
    file = serializers.FileField()
