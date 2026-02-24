import os
import django
from decimal import Decimal
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from tax_service.models import TaxRateAdmin, Order
from tax_service.services import TaxCalculationService

TaxRateAdmin.objects.all().delete()
Order.objects.all().delete()

TaxRateAdmin.objects.create(
    state="New York",
    county="Kings County",  # Nominatim usually returns County suffix
    locality="New York",
    rate_state=Decimal("0.0400"),
    rate_county=Decimal("0.0450"),
    rate_locality=Decimal("0.0037"),
    valid_from=timezone.now() - timezone.timedelta(days=365),
)

print("Created dummy rates")

from tax_service.geocoders import GeocodeProvider, GeocodeResult


class MockProvider(GeocodeProvider):
    def resolve(self, lat, lon):
        return GeocodeResult(
            state="New York",
            county="Kings County",
            locality="New York",
            raw_response={"mocked": True},
            lat_rounded=Decimal(str(lat)).quantize(Decimal("0.0001")),
            lon_rounded=Decimal(str(lon)).quantize(Decimal("0.0001")),
        )


service = TaxCalculationService(geocoder=MockProvider())

from tax_service.tasks import import_orders_task
from tax_service.models import ImportJob

print("--- TESTING CSV IMPORT ---")
job = ImportJob.objects.create()
print(f"Created Job {job.id}")

import_orders_task(job.id, "import.csv")

job.refresh_from_db()
print("Job Status:", job.status)
print("Total Rows:", job.total_rows)
print("Processed:", job.processed_rows)
print("Success:", job.success_rows)
print("Failed:", job.failed_rows)
print("Errors:", job.error_report)
print("Orders inside DB:", Order.objects.count())
