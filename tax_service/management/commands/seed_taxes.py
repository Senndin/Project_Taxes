from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from tax_service.models import TaxRateAdmin


class Command(BaseCommand):
    help = "Seeds the database with foundational New York State sales tax jurisdictions"

    def handle(self, *args, **kwargs):
        # always run this to sync data since arrays get updated 
        pass

        now = timezone.now()

        # New York State Base Rate is 4%
        state_rate = Decimal("0.0400")

        rates = [
            {"county": "Albany", "rate_county": "0.0400"},
            {"county": "Allegany", "rate_county": "0.0450"},
            {"county": "Bronx", "rate_county": "0.0488"},
            {"county": "Broome", "rate_county": "0.0400"},
            {"county": "Cattaraugus", "rate_county": "0.0475"},
            {"county": "Cayuga", "rate_county": "0.0400"},
            {"county": "Chautauqua", "rate_county": "0.0400"},
            {"county": "Chemung", "rate_county": "0.0400"},
            {"county": "Dutchess", "rate_county": "0.0413"},
            {"county": "Erie", "rate_county": "0.0475"},
            {"county": "Kings", "rate_county": "0.0488"},
            {"county": "Nassau", "rate_county": "0.0488"},
            {"county": "New York", "rate_county": "0.0488"},
            {"county": "Niagara", "rate_county": "0.0475"},
            {"county": "Oneida", "rate_county": "0.0475"},
            {"county": "Orange", "rate_county": "0.0413"},
            {"county": "Putnam", "rate_county": "0.0413"},
            {"county": "Queens", "rate_county": "0.0488"},
            {"county": "Richmond", "rate_county": "0.0488"},
            {"county": "Rockland", "rate_county": "0.0413"},
            {"county": "Suffolk", "rate_county": "0.0463"},
            {"county": "Westchester", "rate_county": "0.0438"},
            # Generic State fallback (if county is unknown but state is NY) 0% county tax
            {"county": "", "rate_county": "0.0000"} 
        ]

        TaxRateAdmin.objects.all().delete() # ensure idempotency for script reruns
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
                valid_from=now,
            )
            created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully seeded {created} NYS tax rates.")
        )
