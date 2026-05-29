
import ee
import geemap

# Simple in-memory cache for get_all_regions_data results
_regions_cache = {}


EE_PROJECT = "optical-genre-493118-h1"

try:
    ee.Initialize(project=EE_PROJECT)
except Exception:
    print("⚠️  Earth Engine not initialised – run `earthengine authenticate` first.")


regions_dataset = "WM/geoLab/geoBoundaries/600/ADM1"
map_dataset = "USDOS/LSIB_SIMPLE/2017"
GRACE_DATASET = "NASA/GRACE/MASS_GRIDS/LAND"
SENTINEL2_DATASET = "COPERNICUS/S2_SR_HARMONIZED"
MAX_CLOUD_PERCENT = 20


def get_boundary() -> ee.Geometry:
    # Loads country borders, merges Morocco + Western Sahara into one geometry, returns the unified polygon for clipping
    countries = ee.FeatureCollection(map_dataset)
    morocco_parts = countries.filter(
        ee.Filter.inList("country_na", ["Morocco", "Western Sahara"])
    )
    unified_morocco = morocco_parts.union()
    return unified_morocco.geometry()


def list_regions_morocco() -> list:
    # Fetches all 12 Moroccan admin regions from geoBoundaries, returns a sorted list of region names
    morocco = ee.FeatureCollection(regions_dataset).filter(
        ee.Filter.eq("shapeGroup", "MAR")
    )
    regions = morocco.aggregate_array("shapeName").distinct().sort()
    return regions.getInfo()


def get_region(region_name: str) -> ee.Geometry:
    # Filters geoBoundaries for a single region by name, returns its geometry polygon
    morocco = ee.FeatureCollection(regions_dataset).filter(
        ee.Filter.eq("shapeGroup", "MAR")
    )
    selected_region = morocco.filter(ee.Filter.eq("shapeName", region_name))
    return selected_region.geometry()


def groundwater(year: int) -> geemap.Map:
    # Loads GRACE LWE data for the given year, clips to Morocco, displays on a map with a white-cyan-blue color scale
    grace = (
        ee.ImageCollection(GRACE_DATASET)
        .select("lwe_thickness_csr")
        .filterDate(f"{year}-01-01", f"{year}-12-31")
        .mean()
    )

    morocco_border = get_boundary()
    ground_water = grace.clip(morocco_border)

    gw_vis = {
        "min": -1.5,
        "max": 1.5,
        "palette": ["white", "cyan", "blue"],
    }

    Map = geemap.Map()
    Map.centerObject(morocco_border, 5)
    Map.addLayer(ground_water, gw_vis, f"Groundwater Anomaly {year}")
    Map.add_colorbar(
        vis_params=gw_vis,
        label="Groundwater Anomaly (cm)",
        layer_name="GW_Colorbar",
        orientation="horizontal",
        transparent_bg=True,
    )

    return Map


def get_annual_ndwi_map(year: int) -> geemap.Map:
    # Builds a cloud-free Sentinel-2 composite, computes NDWI (B3-B8)/(B3+B8), clips to Morocco, displays with legend
    morocco_border = get_boundary()

    ndwi_image = (
        ee.ImageCollection(SENTINEL2_DATASET)
        .filterBounds(morocco_border)
        .filterDate(f"{year}-01-01", f"{year}-12-31")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
        .median()
        .normalizedDifference(["B3", "B8"])
        .clip(morocco_border)
    )

    vis_params = {
        "min": -0.5,
        "max": 0.5,
        "palette": [
            "#8B4513", "#D2691E", "#F5DEB3", "#FFFACD",
            "#E0FFFF", "#87CEEB", "#4682B4", "#1E90FF", "#0000CD",
        ],
    }

    Map = geemap.Map()
    Map.centerObject(morocco_border, 6)
    Map.addLayer(ndwi_image, vis_params, f"NDWI {year}")

    legend_dict = {
        "Eau Permanente (0.5)": "#0000CD",
        "Plans d'eau (0.3)": "#1E90FF",
        "Eau peu profonde (0.1)": "#87CEEB",
        "Sol Humide (0.0)": "#FFFACD",
        "Terre Sèche (-0.2)": "#D2691E",
        "Zone Très Sèche (-0.5)": "#8B4513",
    }
    Map.add_legend(
        title=f"Indice NDWI ({year})",
        legend_dict=legend_dict,
        position="bottomright",
        draggable=True,
    )

    return Map


def get_annual_ndvi_map(year: int) -> geemap.Map:
    # Builds a cloud-free Sentinel-2 composite, computes NDVI (B8-B4)/(B8+B4), clips to Morocco, displays with legend
    morocco_border = get_boundary()

    ndvi_image = (
        ee.ImageCollection(SENTINEL2_DATASET)
        .filterBounds(morocco_border)
        .filterDate(f"{year}-01-01", f"{year}-12-31")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
        .median()
        .normalizedDifference(["B8", "B4"])
        .clip(morocco_border)
    )

    vis_params = {
        "min": 0,
        "max": 0.8,
        "palette": [
            "#FFFFFF", "#CE7E45", "#DF923D", "#F1B555", "#FCD163",
            "#99B718", "#74A901", "#66A000", "#529400", "#3E8601",
            "#207401", "#056201",
        ],
    }

    Map = geemap.Map()
    Map.centerObject(morocco_border, 6)
    Map.addLayer(ndvi_image, vis_params, f"NDVI {year}")

    legend_dict = {
        "Forêt Dense (0.7+)": "#056201",
        "Végétation Moyenne (0.5)": "#74A901",
        "Végétation Éparse (0.3)": "#FCD163",
        "Agriculture (0.2)": "#99B718",
        "Sol Nu (0.1)": "#CE7E45",
        "Pas de Végétation (0.0)": "#FFFFFF",
    }
    Map.add_legend(
        title=f"Indice NDVI - Végétation ({year})",
        legend_dict=legend_dict,
        position="bottomright",
    )

    return Map


def groundwater_data(year: int, region: ee.Geometry) -> dict:
    # Loads GRACE data for the year, computes the spatial mean LWE (cm) inside the given region, returns as dict
    grace = (
        ee.ImageCollection(GRACE_DATASET)
        .select("lwe_thickness_csr")
        .filterDate(f"{year}-01-01", f"{year}-12-31")
        .mean()
    )

    data = grace.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=55000,
        maxPixels=1e9,
    )
    return data.getInfo()


def ndwi_data(year: int, region: ee.Geometry) -> dict:
    # Builds a cloud-free Sentinel-2 composite, computes NDWI, clips to the region, returns the spatial mean as dict
    ndwi_image = (
        ee.ImageCollection(SENTINEL2_DATASET)
        .filterBounds(region)
        .filterDate(f"{year}-01-01", f"{year}-12-31")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
        .median()
        .normalizedDifference(["B3", "B8"])
        .clip(region)
        .rename("ndwi")
    )

    data = ndwi_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=1000,
        maxPixels=1e9,
        bestEffort=True,
    )
    return data.getInfo()


def ndvi_data(year: int, region: ee.Geometry) -> dict:
    # Builds a cloud-free Sentinel-2 composite, computes NDVI, clips to the region, returns the spatial mean as dict
    ndvi_image = (
        ee.ImageCollection(SENTINEL2_DATASET)
        .filterBounds(region)
        .filterDate(f"{year}-01-01", f"{year}-12-31")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
        .median()
        .normalizedDifference(["B8", "B4"])
        .clip(region)
        .rename("ndvi")
    )

    data = ndvi_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=1000,
        maxPixels=1e9,
        bestEffort=True,
    )
    return data.getInfo()


def get_all_regions_data(year: int, index: str) -> dict:
    # Computes spatial mean index values for all 12 Moroccan regions at once using reduceRegions to minimize GEE calls
    # Check cache first
    cache_key = f"{index}_{year}"
    if cache_key in _regions_cache:
        return _regions_cache[cache_key]

    regions = ee.FeatureCollection(regions_dataset).filter(ee.Filter.eq("shapeGroup", "MAR"))
    index_lower = index.lower()
    if index_lower == "groundwater":
        image = (
            ee.ImageCollection(GRACE_DATASET)
            .select("lwe_thickness_csr")
            .filterDate(f"{year}-01-01", f"{year}-12-31")
            .mean()
        )
        band_name = "lwe_thickness_csr"
        scale = 55000
    elif index_lower == "ndwi":
        image = (
            ee.ImageCollection(SENTINEL2_DATASET)
            .filterBounds(get_boundary())
            .filterDate(f"{year}-01-01", f"{year}-12-31")
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
            .median()
            .normalizedDifference(["B3", "B8"])
            .rename("ndwi")
        )
        band_name = "ndwi"
        scale = 10000
    elif index_lower == "ndvi":
        image = (
            ee.ImageCollection(SENTINEL2_DATASET)
            .filterBounds(get_boundary())
            .filterDate(f"{year}-01-01", f"{year}-12-31")
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
            .median()
            .normalizedDifference(["B8", "B4"])
            .rename("ndvi")
        )
        band_name = "ndvi"
        scale = 10000
    else:
        raise ValueError(f"Invalid index '{index}'. Use 'groundwater', 'ndwi', or 'ndvi'.")

    reduced = image.reduceRegions(
        collection=regions,
        reducer=ee.Reducer.mean(),
        scale=scale
    )
    
    features = reduced.getInfo().get("features", [])
    result = {}
    for f in features:
        props = f.get("properties", {})
        name = props.get("shapeName")
        val = props.get("mean")
        if val is None:
            val = props.get(band_name)
        result[name] = val

    # Save to cache
    _regions_cache[cache_key] = result
    return result


def get_time_series(region_name: str, index: str, start_year: int, end_year: int) -> dict:
    # Computes a yearly time series server-side in one batched GEE call instead of looping year by year
    region_geom = get_region(region_name)
    index_lower = index.lower()
    years = list(range(start_year, end_year + 1))
    ee_years = ee.List(years)

    if index_lower in ["groundwater", "grace"]:
        def compute_year_gw(y):
            y = ee.Number(y)
            start = ee.Date.fromYMD(y, 1, 1)
            end = ee.Date.fromYMD(y, 12, 31)
            img = (
                ee.ImageCollection(GRACE_DATASET)
                .select("lwe_thickness_csr")
                .filterDate(start, end)
                .mean()
            )
            val = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region_geom,
                scale=55000,
                maxPixels=1e9,
                bestEffort=True,
            ).get("lwe_thickness_csr")
            return ee.Feature(None, {"year": y, "value": val})

        results = ee.FeatureCollection(ee_years.map(compute_year_gw))

    elif index_lower == "ndwi":
        def compute_year_ndwi(y):
            y = ee.Number(y)
            start = ee.Date.fromYMD(y, 1, 1)
            end = ee.Date.fromYMD(y, 12, 31)
            img = (
                ee.ImageCollection(SENTINEL2_DATASET)
                .filterBounds(region_geom)
                .filterDate(start, end)
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
                .median()
                .normalizedDifference(["B3", "B8"])
            )
            val = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region_geom,
                scale=1000,
                maxPixels=1e9,
                bestEffort=True,
            ).get("nd")
            return ee.Feature(None, {"year": y, "value": val})

        results = ee.FeatureCollection(ee_years.map(compute_year_ndwi))

    elif index_lower == "ndvi":
        def compute_year_ndvi(y):
            y = ee.Number(y)
            start = ee.Date.fromYMD(y, 1, 1)
            end = ee.Date.fromYMD(y, 12, 31)
            img = (
                ee.ImageCollection(SENTINEL2_DATASET)
                .filterBounds(region_geom)
                .filterDate(start, end)
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
                .median()
                .normalizedDifference(["B8", "B4"])
            )
            val = img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region_geom,
                scale=1000,
                maxPixels=1e9,
                bestEffort=True,
            ).get("nd")
            return ee.Feature(None, {"year": y, "value": val})

        results = ee.FeatureCollection(ee_years.map(compute_year_ndvi))

    else:
        raise ValueError(f"Invalid index '{index}'. Use 'groundwater', 'ndwi', or 'ndvi'.")

    features = results.getInfo().get("features", [])
    return {
        int(f["properties"]["year"]): f["properties"].get("value")
        for f in features
    }


def get_tile_url(year: int, index: str) -> str:
    # Generates a map tile URL for the specified index and year, allowing the frontend to overlay the satellite layer on a map
    morocco_border = get_boundary()
    index_lower = index.lower()
    
    if index_lower in ["groundwater", "grace"]:
        image = (
            ee.ImageCollection(GRACE_DATASET)
            .select("lwe_thickness_csr")
            .filterDate(f"{year}-01-01", f"{year}-12-31")
            .mean()
            .clip(morocco_border)
        )
        vis_params = {
            "min": -1.5,
            "max": 1.5,
            "palette": ["white", "cyan", "blue"],
        }
    elif index_lower == "ndwi":
        image = (
            ee.ImageCollection(SENTINEL2_DATASET)
            .filterBounds(morocco_border)
            .filterDate(f"{year}-01-01", f"{year}-12-31")
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
            .median()
            .normalizedDifference(["B3", "B8"])
            .clip(morocco_border)
        )
        vis_params = {
            "min": -0.5,
            "max": 0.5,
            "palette": [
                "#8B4513", "#D2691E", "#F5DEB3", "#FFFACD",
                "#E0FFFF", "#87CEEB", "#4682B4", "#1E90FF", "#0000CD",
            ],
        }
    elif index_lower == "ndvi":
        image = (
            ee.ImageCollection(SENTINEL2_DATASET)
            .filterBounds(morocco_border)
            .filterDate(f"{year}-01-01", f"{year}-12-31")
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
            .median()
            .normalizedDifference(["B8", "B4"])
            .clip(morocco_border)
        )
        vis_params = {
            "min": 0,
            "max": 0.8,
            "palette": [
                "#FFFFFF", "#CE7E45", "#DF923D", "#F1B555", "#FCD163",
                "#99B718", "#74A901", "#66A000", "#529400", "#3E8601",
                "#207401", "#056201",
            ],
        }
    else:
        raise ValueError(f"Invalid index '{index}'. Use 'groundwater', 'ndwi', or 'ndvi'.")
        
    map_id = image.getMapId(vis_params)
    return map_id["tile_fetcher"].url_format

