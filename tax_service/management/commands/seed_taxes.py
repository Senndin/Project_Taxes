from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from tax_service.models import TaxRateAdmin


class Command(BaseCommand):
    help = "Seeds the database with foundational New York State sales tax jurisdictions"

    def handle(self, *args, **kwargs):
        # always run this to sync data since arrays get updated
        pass

        # Use a fixed historical date so rates apply to orders with ANY timestamp,
        # including past-dated CSV imports. This was the root cause of tax=0 bug:
        # timezone.now() meant rates only matched orders from "right now" onwards.
        from datetime import datetime

        valid_from_date = timezone.make_aware(datetime(2020, 1, 1))

        # New York State Base Rate is 4%
        state_rate = Decimal("0.0400")

        rates = [
            {"county": "Albany County", "rate_county": "0.0400"},
            {"county": "Allegany County", "rate_county": "0.0450"},
            {"county": "Bronx County", "rate_county": "0.0488"},
            {"county": "Broome County", "rate_county": "0.0400"},
            {"county": "Cattaraugus County", "rate_county": "0.0475"},
            {"county": "Cayuga County", "rate_county": "0.0400"},
            {"county": "Chautauqua County", "rate_county": "0.0400"},
            {"county": "Chemung County", "rate_county": "0.0400"},
            {"county": "Dutchess County", "rate_county": "0.0413"},
            {"county": "Erie County", "rate_county": "0.0475"},
            {"county": "Kings County", "rate_county": "0.0488"},
            {"county": "Nassau County", "rate_county": "0.0488"},
            {"county": "New York County", "rate_county": "0.0488"},
            {"county": "Niagara County", "rate_county": "0.0475"},
            {"county": "Oneida County", "rate_county": "0.0475"},
            {"county": "Orange County", "rate_county": "0.0413"},
            {"county": "Putnam County", "rate_county": "0.0413"},
            {"county": "Queens County", "rate_county": "0.0488"},
            {"county": "Richmond County", "rate_county": "0.0488"},
            {"county": "Rockland County", "rate_county": "0.0413"},
            {"county": "Suffolk County", "rate_county": "0.0463"},
            {"county": "Westchester County", "rate_county": "0.0438"},
            # Generic State fallback (if county is unknown but state is NY) 0% county tax
            {"county": "", "rate_county": "0.0000"},
        ]

        TaxRateAdmin.objects.all().delete()  # ensure idempotency for script reruns
        created = 0
        for data in rates:
            TaxRateAdmin.objects.create(
                state="New York",
                county=data["county"],
                locality=None,
                rate_state=state_rate,
                rate_county=Decimal(data["rate_county"]),
                rate_locality=Decimal("0.0000"),
                rate_special=None,
                valid_from=valid_from_date,
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {created} NYS tax rates.")
        )
