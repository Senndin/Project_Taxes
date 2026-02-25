from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction, models
from django.utils import timezone
from .models import Order, TaxRateAdmin
from .geocoders import GeocodeProvider, GeocodeResult, LocalNYSProvider
import logging

logger = logging.getLogger(__name__)


class TaxCalculationService:
    def __init__(self, geocoder=None):
        self.geocoder = geocoder or LocalNYSProvider()

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
            breakdown = []
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

            state_tax = (subtotal_dec * rate_record.rate_state).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            county_tax = (subtotal_dec * rate_record.rate_county).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            breakdown = [
                {
                    "name": rate_record.state,
                    "rate": str(rate_record.rate_state),
                    "tax_amount": str(state_tax),
                },
                {
                    "name": rate_record.county
                    if rate_record.county
                    else "County (Generic)",
                    "rate": str(rate_record.rate_county),
                    "tax_amount": str(county_tax),
                },
            ]

            if rate_record.locality and rate_record.rate_locality > 0:
                jurisdictions.append(rate_record.locality)
                locality_tax = (subtotal_dec * rate_record.rate_locality).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                breakdown.append(
                    {
                        "name": rate_record.locality,
                        "rate": str(rate_record.rate_locality),
                        "tax_amount": str(locality_tax),  # type: ignore
                    }
                )

            if rate_record.rate_special and rate_record.rate_special > 0:
                jurisdictions.append("Special District")
                special_tax = (subtotal_dec * rate_record.rate_special).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                breakdown.append(
                    {
                        "name": "Special District",
                        "rate": str(rate_record.rate_special),
                        "tax_amount": str(special_tax),  # type: ignore
                    }
                )

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
        qs = TaxRateAdmin.objects.filter(
            state__iexact=state, valid_from__lte=date
        ).filter(models.Q(valid_to__isnull=True) | models.Q(valid_to__gte=date))

        logger.info(f"fetch_rate cascade started for state='{state}', county='{county}', locality='{locality}'")

        # 1. Try matching exact locality first
        if locality:
            exact_match = qs.filter(
                county__iexact=county, locality__iexact=locality
            ).first()
            if exact_match:
                logger.info(f"Resolution success: Level 1 (Exact Locality Match) - Found: {exact_match.county} {exact_match.locality}")
                return exact_match

        # 2. Try exact match with normalized county
        if county:
            base_county_match = qs.filter(county__iexact=county).first()
            if base_county_match:
                logger.info(f"Resolution success: Level 2 (Exact County Match) - Found: {base_county_match.county}")
                return base_county_match

            # 3. Fuzzy match: icontains safely without suffix
            clean_county = county.replace(" County", "").replace(" City", "").strip()
            if clean_county:
                fuzzy_match = qs.filter(county__icontains=clean_county).first()
                if fuzzy_match:
                    logger.info(f"Resolution success: Level 3 (Fuzzy County Match) - '{county}' matched to '{fuzzy_match.county}'")
                    return fuzzy_match

        # 4. Fallback to generic State-level rate (empty county field)
        state_fallback = qs.filter(county__exact="").first()
        if state_fallback:
            logger.info(f"Resolution success: Level 4 (State Generic Fallback match) - Returning 4.0% base rate. State={state}")
            return state_fallback

        # 5. Complete fallback (just state match)
        logger.warning(f"Resolution failed: Exhausted all tiers for {state}, {county}. Returning first available base rate.")
        return qs.first()
