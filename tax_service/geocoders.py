import json
import os
from decimal import Decimal, ROUND_HALF_UP
from django.conf import settings
from .utils.geo_math import find_containing_feature
import logging

logger = logging.getLogger(__name__)


def normalize_county(county_str: str, locality_str: str = "") -> str:
    """
    Standardizes county strings:
    - Removes "County" suffix
    - Maps NYC boroughs to their canonical county names
    """
    if not county_str:
        if locality_str in ['New York City', 'New York', 'Manhattan']:
            return "New York"
        elif locality_str == 'Brooklyn':
            return "Kings"
        elif locality_str == 'Queens':
            return "Queens"
        elif locality_str == 'Bronx':
            return "Bronx"
        elif locality_str == 'Staten Island':
            return "Richmond"
        return ""
    
    county = county_str.strip()
    if county.lower().endswith(" county"):
        county = county[:-7].strip()
    
    # Also standardize if the provider returned the borough as the county directly
    if county == "Manhattan": return "New York"
    if county == "Brooklyn": return "Kings"
    if county == "Staten Island": return "Richmond"

    return county


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


class VectorPolygonProvider(GeocodeProvider):
    """
    Custom Point-in-Polygon spatial resolver using pure math instead of third-party APIs.
    """
    provider_name = "vector_polygon"
    _geojson_data = None

    @classmethod
    def get_geojson(cls):
        # Cache GeoJSON in memory across calculations so we don't disk-read 200 times
        if cls._geojson_data is None:
            # Assumes data folder is in BASE_DIR (one level up from tax_service)
            # Actually, standard django base dir is Project_Taxes
            data_path = os.path.join(settings.BASE_DIR, "data", "nys_counties.geojson")
            with open(data_path, "r", encoding="utf-8") as f:
                cls._geojson_data = json.load(f)
        return cls._geojson_data

    def resolve(self, lat: float, lon: float) -> GeocodeResult:
        lat_rounded = Decimal(str(lat)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        lon_rounded = Decimal(str(lon)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

        data = self.get_geojson()
        feature = find_containing_feature(lon, lat, data)

        assigned_county = ""
        assigned_state = "New York" # Since the dataset is strictly NY boundaries
        assigned_locality = ""

        if feature:
            props = feature.get('properties', {})
            raw_county = props.get('name', '')
            assigned_county = normalize_county(raw_county)

        return GeocodeResult(
            state=assigned_state if assigned_county else "Unknown State",
            county=assigned_county if assigned_county else "Unknown County",
            locality=assigned_locality,
            raw_response={"feature": feature.copy() if feature else {}},
            lat_rounded=lat_rounded,
            lon_rounded=lon_rounded
        )
