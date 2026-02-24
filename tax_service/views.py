from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from .models import Order, ImportJob
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    ImportJobSerializer,
    ImportJobCreateSerializer,
)
from .services import TaxCalculationService
from .tasks import import_orders_task


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = TaxCalculationService()
        order = service.process_order(
            lat=data["lat"],
            lon=data["lon"],
            subtotal=data["subtotal"],
            order_timestamp=data.get("timestamp"),
        )

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def clear(self, request):
        Order.objects.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["post"], parser_classes=[MultiPartParser])
    def import_csv(self, request):
        serializer = ImportJobCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file_obj = serializer.validated_data["file"]

        job = ImportJob.objects.create()
        
        try:
            file_content = file_obj.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            file_content = file_obj.read().decode('latin-1')

        # Fire off celery task passing the content directly via Redis.
        # This completely avoids Heroku's ephemeral/isolated filesystem issues.
        import_orders_task.delay(job.id, file_content)

        return Response(ImportJobSerializer(job).data, status=status.HTTP_202_ACCEPTED)


class ImportJobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ImportJob.objects.all().order_by("-created_at")
    serializer_class = ImportJobSerializer
