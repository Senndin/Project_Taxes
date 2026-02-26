from django.contrib import admin
from .models import TaxRateAdmin, Order, ImportJob


@admin.register(TaxRateAdmin)
class TaxRateAdminAdmin(admin.ModelAdmin):
    list_display = (
        "state",
        "county",
        "locality",
        "rate_state",
        "rate_county",
        "rate_locality",
        "rate_special",
        "valid_from",
        "valid_to",
    )
    list_filter = ("state", "county")
    search_fields = ("county", "locality")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "geo_state",
        "geo_county",
        "subtotal",
        "composite_rate",
        "tax_amount",
        "total_amount",
        "created_at",
    )
    list_filter = ("geo_state", "geo_county", "geo_source")
    search_fields = ("geo_county", "geo_locality")
    readonly_fields = ("breakdown", "jurisdictions", "geo_raw_response")


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "status",
        "total_rows",
        "success_rows",
        "failed_rows",
        "created_at",
        "finished_at",
    )
    list_filter = ("status",)
    readonly_fields = ("error_report",)
