def point_in_polygon(point, polygon):
    """
    Ray casting algorithm to check if a point is inside a polygon.
    point: (lon, lat) tuple
    polygon: list of linear rings. The first ring is the exterior boundary; 
             subsequent rings are holes. A ring is a list of [lon, lat] coordinates.
    """
    x, y = point
    
    def is_inside_ring(ring):
        inside = False
        n = len(ring)
        if n == 0:
            return False
            
        p1x, p1y = ring[0]
        for i in range(1, n + 1):
            p2x, p2y = ring[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                            if p1x == p2x or x <= xinters:
                                inside = not inside
            p1x, p1y = p2x, p2y
        return inside

    # Check exterior ring (must be inside)
    if not polygon or not is_inside_ring(polygon[0]):
        return False
        
    # Check holes (must NOT be inside any hole)
    for hole in polygon[1:]:
        if is_inside_ring(hole):
            return False
            
    return True


def point_in_multipolygon(point, multipolygon):
    """
    Check if point is inside any of the polygons in a multipolygon.
    multipolygon: list of polygons
    """
    for polygon in multipolygon:
        if point_in_polygon(point, polygon):
            return True
    return False


def find_containing_feature(lon, lat, geojson_data):
    """
    Iterate over GeoJSON features to find the one containing the point.
    Returns the feature dictionary or None.
    """
    point = (lon, lat)
    for feature in geojson_data.get('features', []):
        geom = feature.get('geometry')
        if not geom:
            continue
            
        geom_type = geom.get('type')
        coords = geom.get('coordinates', [])
        
        if geom_type == 'Polygon':
            if point_in_polygon(point, coords):
                return feature
        elif geom_type == 'MultiPolygon':
            if point_in_multipolygon(point, coords):
                return feature
                
    return None
