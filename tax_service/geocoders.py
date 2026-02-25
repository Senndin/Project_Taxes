import requests
import time
from decimal import Decimal, ROUND_HALF_UP
from .models import GeocodeCache
import logging

logger = logging.getLogger(__name__)


class GeocodeResult:
    def __init__(self, state, county, locality, raw_response, lat_rounded, lon_rounded):
        self.state = state
        self.county = county
        self.locality = locality
        self.raw_response = raw_response
        self.lat_rounded = lat_rounded
        self.lon_rounded = lon_rounded


class GeocodeProvider:
    provider_name = "unknown"

    def resolve(self, lat: float, lon: float) -> GeocodeResult:
        raise NotImplementedError("Subclasses must implement resolve")


class NominatimProvider(GeocodeProvider):
    # Base Nominatim URL
    URL = "https://nominatim.openstreetmap.org/reverse"
    provider_name = "nominatim"

    def resolve(self, lat: float, lon: float) -> GeocodeResult:
        # Round to 4 decimal places (approx 11m precision)
        lat_rounded = Decimal(str(lat)).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        lon_rounded = Decimal(str(lon)).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )

        cache_key = f"{self.provider_name}_{lat_rounded}_{lon_rounded}"

        # 1. Check Local DB Cache
        cached = GeocodeCache.objects.filter(cache_key=cache_key).first()
        if cached:
            return GeocodeResult(
                state=cached.state,
                county=cached.county,
                locality=cached.locality,
                raw_response=cached.raw_response,
                lat_rounded=lat_rounded,
                lon_rounded=lon_rounded,
            )

        # 2. Hard Rate Limit for single requests (Simplistic sleep to respect 1 req/sec)
        # Note: In a true highly-concurrent API, you replace this with Redis-backed rate limiting.
        time.sleep(1.1)

        headers = {"User-Agent": "NYSTaxCalculator/1.0 (denischernokur@example.com)"}
        params = {
            "lat": lat,
            "lon": lon,
            "format": "json",
            "zoom": 18,
            "addressdetails": 1,
        }

        # 3. Call Nominatim
        response = requests.get(self.URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        address = data.get("address", {})

        # 4. Normalize extraction
        # Nominatim returns varying keys for locality/city
        state = address.get("state", "")
        county = address.get("county", "")
        locality = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("hamlet")
        )

        if not state:
            # Maybe outside US or ocean
            state = "UNKNOWN"
            county = "UNKNOWN"

        result = GeocodeResult(
            state=state,
            county=county,
            locality=locality,
            raw_response=data,
            lat_rounded=lat_rounded,
            lon_rounded=lon_rounded,
        )

        # 5. Save to Cache
        GeocodeCache.objects.create(
            cache_key=cache_key,
            provider=self.provider_name,
            lat_rounded=lat_rounded,
            lon_rounded=lon_rounded,
            state=result.state,
            county=result.county,
            locality=result.locality,
            raw_response=result.raw_response,
        )

        return result

class LocalNYSProvider(GeocodeProvider):
    provider_name = "local_nys"

    def resolve(self, lat: float, lon: float) -> GeocodeResult:
        from decimal import Decimal
        import reverse_geocoder as rg
        
        # Search returns a list of dictionaries. For example:
        # [{'lat': '41.92704', 'lon': '-73.99736', 'name': 'Kingston', 'admin1': 'New York', 'admin2': 'Ulster County', 'cc': 'US'}]
        results = rg.search((lat, lon))
        
        assigned_state = "Unknown State"
        assigned_county = "Unknown County"
        assigned_locality = "Unknown Locality"
        assigned_suburb = ""
        
        if results and len(results) > 0:
            match = results[0]
            assigned_state = match.get('admin1', 'Unknown State')
            assigned_county = match.get('admin2', 'Unknown County')
            assigned_locality = match.get('name', 'Unknown Locality')
            
        return GeocodeResult(
            state=assigned_state,
            county=assigned_county,
            locality=assigned_locality,
            raw_response={"address": {"city": assigned_locality, "county": assigned_county, "state": assigned_state}},
            lat_rounded=Decimal(str(lat)).quantize(Decimal("0.0001")),
            lon_rounded=Decimal(str(lon)).quantize(Decimal("0.0001")),
        )
