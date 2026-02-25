from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from tax_service.models import TaxRateAdmin


class Command(BaseCommand):
    help = "Seeds the database with foundational New York State sales tax jurisdictions"

    def handle(self, *args, **kwargs):
        if TaxRateAdmin.objects.count() > 10:
            self.stdout.write(self.style.WARNING("Database already seeded. Skipping."))
            return

        now = timezone.now()

        # New York State Base Rate is 4%
        state_rate = Decimal("0.0400")

        rates = [
            # Generic State fallback (if county is unknown but state is NY)
            {
                "county": "",
                "locality": None,
                "rate_county": "0.0400",
                "rate_special": "0.0000",
            },
            # Major Counties
            {
                "county": "Kings County",
                "locality": "New York",
                "rate_county": "0.0450",
                "rate_special": "0.0037",
            },  # Brooklyn
            {
                "county": "New York County",
                "locality": "New York",
                "rate_county": "0.0450",
                "rate_special": "0.0037",
            },  # Manhattan
            {
                "county": "Queens County",
                "locality": "New York",
                "rate_county": "0.0450",
                "rate_special": "0.0037",
            },  # Queens
            {
                "county": "Bronx County",
                "locality": "New York",
                "rate_county": "0.0450",
                "rate_special": "0.0037",
            },  # Bronx
            {
                "county": "Richmond County",
                "locality": "New York",
                "rate_county": "0.0450",
                "rate_special": "0.0037",
            },  # Staten Island
            {
                "county": "Erie County",
                "locality": None,
                "rate_county": "0.0475",
                "rate_special": "0.0000",
            },
            {
                "county": "Albany County",
                "locality": None,
                "rate_county": "0.0400",
                "rate_special": "0.0000",
            },
            {
                "county": "Monroe County",
                "locality": None,
                "rate_county": "0.0400",
                "rate_special": "0.0000",
            },
            {
                "county": "Onondaga County",
                "locality": None,
                "rate_county": "0.0400",
                "rate_special": "0.0000",
            },
            {
                "county": "Westchester County",
                "locality": None,
                "rate_county": "0.0437",
                "rate_special": "0.0000",
            },
            {
                "county": "Nassau County",
                "locality": None,
                "rate_county": "0.0462",
                "rate_special": "0.0000",
            },
            {
                "county": "Suffolk County",
                "locality": None,
                "rate_county": "0.0462",
                "rate_special": "0.0000",
            },
        ]

        created = 0
        for data in rates:
            TaxRateAdmin.objects.create(
                state="New York",
                county=data["county"],
                locality=data["locality"],
                rate_state=state_rate,
                rate_county=Decimal(data["rate_county"]),
                rate_locality=Decimal("0.0000"),
                rate_special=Decimal(data["rate_special"]),
                valid_from=now,
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {created} NYS tax rates.")
        )
