from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction, models
from django.utils import timezone
from .models import Order, TaxRateAdmin
from .geocoders import GeocodeProvider, GeocodeResult
import logging

logger = logging.getLogger(__name__)


class MockProvider(GeocodeProvider):
    provider_name = "mock"

    def resolve(self, lat: float, lon: float) -> GeocodeResult:
        from decimal import Decimal

        return GeocodeResult(
            state="New York",
            county="Kings County",
            locality="New York",
            raw_response={"mocked": True},
            lat_rounded=Decimal(str(lat)).quantize(Decimal("0.0001")),
            lon_rounded=Decimal(str(lon)).quantize(Decimal("0.0001")),
        )


class TaxCalculationService:
    def __init__(self, geocoder=None):
        self.geocoder = geocoder or MockProvider()

    @transaction.atomic
    def process_order(
        self, lat: float, lon: float, subtotal: str, order_timestamp=None
    ) -> Order:
        if order_timestamp is None:
            order_timestamp = timezone.now()

        subtotal_dec = Decimal(str(subtotal))

        # 1. Resolve Geo limits
        geo_result = self.geocoder.resolve(lat, lon)

        # 2. Fetch Rate explicitly
        rate_record = self.fetch_rate(
            state=geo_result.state,
            county=geo_result.county,
            locality=geo_result.locality,
            date=order_timestamp,
        )

        if not rate_record:
            # Fallback for out-of-state or completely unknown zones
            # We treat this as 0% tax nexus.
            composite_rate = Decimal("0.0000")
            breakdown = {"notice": "No tax nexus found for given coordinates."}
            jurisdictions = []
        else:
            # 3. Compute Composite
            composite_rate = (
                rate_record.rate_state
                + rate_record.rate_county
                + rate_record.rate_locality
                + (rate_record.rate_special or Decimal("0.0000"))
            )

            # 5. Build Breakdown
            jurisdictions = [rate_record.state, rate_record.county]
            breakdown = {
                "state": {
                    "name": rate_record.state,
                    "rate": str(rate_record.rate_state),
                },
                "county": {
                    "name": rate_record.county,
                    "rate": str(rate_record.rate_county),
                },
            }

            if rate_record.locality and rate_record.rate_locality > 0:
                jurisdictions.append(rate_record.locality)
                breakdown["locality"] = {
                    "name": rate_record.locality,
                    "rate": str(rate_record.rate_locality),
                }

            if rate_record.rate_special and rate_record.rate_special > 0:
                jurisdictions.append("Special District")
                breakdown["special"] = {
                    "name": "Special District",
                    "rate": str(rate_record.rate_special),
                }

        # 4. Rounding Rules - round half up to 2 decimal places
        tax_amount = (subtotal_dec * composite_rate).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total_amount = subtotal_dec + tax_amount

        # Determine source (was it cached or fresh hit?)
        # Since our NominatimProvider saves to DB during fresh request but we didn't explicitly separate cache-hit vs miss in return,
        # we can just log the provider name as the source format.
        geo_source = getattr(
            self.geocoder, "provider_name", "unknown"
        )  # Dynamically pull the provider name

        # 6. Create Order
        order = Order.objects.create(
            lat=lat,
            lon=lon,
            subtotal=subtotal_dec,
            order_timestamp=order_timestamp,
            geo_state=geo_result.state,
            geo_county=geo_result.county,
            geo_locality=geo_result.locality,
            geo_source=geo_source,
            geo_raw_response=geo_result.raw_response,
            composite_rate=composite_rate,
            tax_amount=tax_amount,
            total_amount=total_amount,
            jurisdictions=jurisdictions,
            breakdown=breakdown,
        )

        return order

    def fetch_rate(self, state, county, locality, date):
        # Base query for the exact date interval
        # If State is not NY (e.g., 'New York' vs something else), handle properly according to actual state nomenclature
        # We assume the database is pre-filled with correctly normalized names.

        qs = TaxRateAdmin.objects.filter(
            state__iexact=state, valid_from__lte=date
        ).filter(models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=date))

        # Try matching exact locality first
        if locality:
            exact_match = qs.filter(
                county__iexact=county, locality__iexact=locality
            ).first()
            if exact_match:
                return exact_match

        # Fallback to county-level generic rate (locality is null or empty)
        base_county_match = (
            qs.filter(county__iexact=county)
            .filter(models.Q(locality__isnull=True) | models.Q(locality__exact=""))
            .first()
        )

        if base_county_match:
            return base_county_match

        # Complete fallback (just state match)
        return qs.first()
