import json
import os
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from .utils.geo_math import find_containing_feature
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

        lat_rounded = Decimal(str(lat)).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        lon_rounded = Decimal(str(lon)).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )

        # Search returns a list of dictionaries. For example:
        # [{'lat': '41.92704', 'lon': '-73.99736', 'name': 'Kingston', 'admin1': 'New York', 'admin2': 'Ulster County', 'cc': 'US'}]
        # mode=1 explicitly forces single-process mode because Celery daemons cannot spawn children.
        results = rg.search((lat, lon), mode=1)

        assigned_state = "Unknown State"
        assigned_county = "Unknown County"
        assigned_locality = "Unknown Locality"
        raw_match = {}

        if results and len(results) > 0:
            match = results[0]
            raw_match = match.copy()
            assigned_state = match.get("admin1", "Unknown State")
            assigned_locality = match.get("name", "Unknown Locality")

            # The KD-Tree dataset frequently leaves admin2 blank for NYC boroughs.
            raw_county = match.get("admin2", "")

            if not raw_county:
                # Fallback heuristics for New York City coordinates which lack county data in the offline array
                if assigned_locality in ["New York City", "New York", "Manhattan"]:
                    assigned_county = "New York County"
                elif assigned_locality == "Brooklyn":
                    assigned_county = "Kings County"
                elif assigned_locality == "Queens":
                    assigned_county = "Queens County"
                elif assigned_locality == "Bronx":
                    assigned_county = "Bronx County"
                elif assigned_locality == "Staten Island":
                    assigned_county = "Richmond County"
                else:
                    assigned_county = "Unknown County"
            else:
                assigned_county = raw_county
                # Normalize "Kings" -> "Kings County" to strictly match DB seed
                if "County" not in assigned_county and assigned_state == "New York":
                    assigned_county = f"{assigned_county} County"

        return GeocodeResult(
            state=assigned_state if assigned_county else "Unknown State",
            county=assigned_county if assigned_county else "Unknown County",
            locality=assigned_locality,
            raw_response={"match": raw_match},
            lat_rounded=lat_rounded,
            lon_rounded=lon_rounded,
        )


class VectorPolygonProvider(GeocodeProvider):
    """
    100% Offline geocoder. Визначає округ NYS за координатами
    через point-in-polygon пошук по GeoJSON-полігонах.
    Не потребує зовнішніх API чи додаткових C-бібліотек.
    """

    provider_name = "vector_polygon"
    _geojson_cache = None  # Синглтон — завантажується один раз

    @classmethod
    def _load_geojson(cls):
        if cls._geojson_cache is None:
            geojson_path = os.path.join(
                settings.BASE_DIR, "data", "nys_counties.geojson"
            )
            with open(geojson_path, "r") as f:
                cls._geojson_cache = json.load(f)
            logger.info(
                f"Loaded {len(cls._geojson_cache.get('features', []))} "
                f"county polygons from {geojson_path}"
            )
        return cls._geojson_cache

    def resolve(self, lat: float, lon: float) -> GeocodeResult:
        lat_rounded = Decimal(str(lat)).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )
        lon_rounded = Decimal(str(lon)).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP
        )

        geojson_data = self._load_geojson()
        feature = find_containing_feature(
            float(lon_rounded), float(lat_rounded), geojson_data
        )

        if feature:
            props = feature.get("properties", {})
            county_name = props.get("name", "Unknown County")
            return GeocodeResult(
                state="New York",
                county=county_name,
                locality=None,
                raw_response={
                    "feature": {"name": county_name, "geoid": props.get("geoid", "")}
                },
                lat_rounded=lat_rounded,
                lon_rounded=lon_rounded,
            )

        # Координати поза NYS → 0% податок (no nexus)
        return GeocodeResult(
            state="Out of State",
            county="",
            locality=None,
            raw_response={"error": "Point not within any NYS county polygon"},
            lat_rounded=lat_rounded,
            lon_rounded=lon_rounded,
        )
