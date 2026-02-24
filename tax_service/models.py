from django.db import models
from django.utils import timezone
from decimal import Decimal


class GeocodeCache(models.Model):
    # Composite key like "nominatim_40.7128_-74.0060"
    cache_key = models.CharField(max_length=255, unique=True, db_index=True)
    provider = models.CharField(max_length=50, default="nominatim")
    lat_rounded = models.DecimalField(max_digits=9, decimal_places=4, db_index=True)
    lon_rounded = models.DecimalField(max_digits=9, decimal_places=4, db_index=True)
    state = models.CharField(max_length=100)
    county = models.CharField(max_length=100)
    locality = models.CharField(max_length=100, null=True, blank=True)
    raw_response = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "geocode_cache"


class TaxRateAdmin(models.Model):
    state = models.CharField(max_length=50, db_index=True)
    county = models.CharField(max_length=100, db_index=True)
    locality = models.CharField(max_length=100, null=True, blank=True, db_index=True)

    rate_state = models.DecimalField(max_digits=6, decimal_places=4)
    rate_county = models.DecimalField(max_digits=6, decimal_places=4)
    rate_locality = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    rate_special = models.DecimalField(
        max_digits=6, decimal_places=4, null=True, blank=True
    )

    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "tax_rate_admin"
        indexes = [
            models.Index(
                fields=["state", "county", "locality", "valid_from", "valid_to"]
            ),
        ]


class Order(models.Model):
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lon = models.DecimalField(max_digits=9, decimal_places=6)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    order_timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    geo_state = models.CharField(max_length=100)
    geo_county = models.CharField(max_length=100)
    geo_locality = models.CharField(max_length=100, null=True, blank=True)
    geo_source = models.CharField(max_length=50)  # 'cache', 'nominatim'
    geo_raw_response = models.JSONField()

    composite_rate = models.DecimalField(max_digits=6, decimal_places=4)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    jurisdictions = models.JSONField()  # List of jurisdictions applied
    breakdown = models.JSONField()  # Detailed breakdown of rates
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order"


class ImportJob(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("COMPLETED", "Completed"),
        ("FAILED", "Failed"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    total_rows = models.IntegerField(default=0)
    processed_rows = models.IntegerField(default=0)
    success_rows = models.IntegerField(default=0)
    failed_rows = models.IntegerField(default=0)
    error_report = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "import_job"
