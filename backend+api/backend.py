
import ee
import geemap
import json
import os
from concurrent.futures import ThreadPoolExecutor

# Simple in-memory cache for get_all_regions_data results
_regions_cache = {}
# Simple in-memory cache for tile URLs
_tile_url_cache = {}


EE_PROJECT = "optical-genre-493118-h1"

try:
    ee.Initialize(project=EE_PROJECT)
except Exception:
    print("⚠️  Earth Engine not initialised – run `earthengine authenticate` first.")


regions_dataset = "WM/geoLab/geoBoundaries/600/ADM1"

# Cache variable for local regions
_morocco_regions_fc = None

def get_morocco_regions() -> ee.FeatureCollection:
    global _morocco_regions_fc
    if _morocco_regions_fc is not None:
        return _morocco_regions_fc
        
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ma_json_path = os.path.normpath(os.path.join(base_dir, "..", "src", "data", "ma_simplified.json"))
    
    with open(ma_json_path, 'r', encoding='utf-8') as f:
        geojson = json.load(f)
        
    ee_features = []
    for feature in geojson['features']:
        name = feature['properties']['name']
        region_id = feature['properties']['id']
        ee_geom = ee.Geometry(feature['geometry'])
        ee_feat = ee.Feature(ee_geom, {
            "shapeName": name,
            "shapeGroup": "MAR",
            "id": region_id
        })
        ee_features.append(ee_feat)
        
    _morocco_regions_fc = ee.FeatureCollection(ee_features)
    return _morocco_regions_fc
map_dataset = "USDOS/LSIB_SIMPLE/2017"
GRACE_DATASET = "NASA/GRACE/MASS_GRIDS_V04/MASCON"
GLDAS_DATASET = "NASA/GLDAS/V021/NOAH/G025/T3H"
SENTINEL2_DATASET = "COPERNICUS/S2_HARMONIZED"
MAX_CLOUD_PERCENT = 30

# GRACE MASCON v04 uses 2004-2009 as the baseline period for anomalies
GRACE_BASELINE_START = 2004
GRACE_BASELINE_END = 2009

# GLDAS bands used to estimate non-groundwater water storage
_GLDAS_BANDS = [
    "SoilMoi0_10cm_inst",
    "SoilMoi10_40cm_inst",
    "SoilMoi40_100cm_inst",
    "SoilMoi100_200cm_inst",
    "SWE_inst",
    "CanopInt_inst",
]

# Cache for the GLDAS baseline mean (computed once, reused forever)
_gldas_baseline_image = None


def _get_gldas_baseline() -> ee.Image:
    """Returns the mean GLDAS surface water storage over the GRACE baseline period (2004-2009).
    Result is the sum of soil moisture + SWE + canopy in cm of water equivalent."""
    global _gldas_baseline_image
    if _gldas_baseline_image is not None:
        return _gldas_baseline_image

    baseline = (
        ee.ImageCollection(GLDAS_DATASET)
        .select(_GLDAS_BANDS)
        .filterDate(f"{GRACE_BASELINE_START}-01-01", f"{GRACE_BASELINE_END + 1}-01-01")
        .mean()
    )
    # Sum all components and convert kg/m² (mm) to cm
    _gldas_baseline_image = baseline.reduce(ee.Reducer.sum()).divide(10).rename("surface_storage")
    return _gldas_baseline_image


def _get_gldas_annual(year: int) -> ee.Image:
    """Returns the annual mean GLDAS surface water storage for a given year, in cm."""
    annual = (
        ee.ImageCollection(GLDAS_DATASET)
        .select(_GLDAS_BANDS)
        .filterDate(f"{year}-01-01", f"{year + 1}-01-01")
        .mean()
    )
    return annual.reduce(ee.Reducer.sum()).divide(10).rename("surface_storage")


def get_gwsa_image(year: int) -> ee.Image:
    """Computes true Groundwater Storage Anomaly (GWSA) for a given year.
    GWSA = GRACE_TWSA - (GLDAS_annual - GLDAS_baseline)
    Returns a single-band ee.Image named 'gwsa'."""
    # 1. GRACE Total Water Storage Anomaly (already an anomaly vs 2004-2009 baseline)
    grace_twsa = (
        ee.ImageCollection(GRACE_DATASET)
        .select("lwe_thickness")
        .filterDate(f"{year}-01-01", f"{year + 1}-01-01")
        .mean()
    )

    # 2. GLDAS surface storage anomaly (annual - baseline), in cm
    gldas_baseline = _get_gldas_baseline()
    gldas_annual = _get_gldas_annual(year)
    gldas_anomaly = gldas_annual.subtract(gldas_baseline)

    # 3. Subtract to isolate groundwater: GWSA = TWSA - surface_anomaly
    gwsa = grace_twsa.subtract(gldas_anomaly).rename("gwsa")

    return gwsa


# OpenLandMap sand fraction dataset used to derive spatially-varying Specific Yield (Sy)
# Sy varies from ~0.046 (clay) to ~0.27 (sand) based on the USGS empirical relationship
OPENLANDMAP_SAND = "OpenLandMap/SOL/SOL_SAND-WFRACTION_USDA-3A1A1A_M/v02"

# Cache for the Sy image (computed once, reused forever)
_sy_image = None


def _get_specific_yield_map() -> ee.Image:
    """Builds a spatially-varying Specific Yield (Sy) map from OpenLandMap soil sand fraction.
    Uses the USGS empirical pedotransfer function: Sy = 0.042 + 0.0023 × sand%
    where sand% is the weight fraction of sand (0-100) at 0-10cm depth.
    Resolution: 250m. Returns a single-band ee.Image named 'sy'."""
    global _sy_image
    if _sy_image is not None:
        return _sy_image

    # Load sand fraction (%) at shallowest depth layer (b0 = 0 cm)
    sand_pct = ee.Image(OPENLANDMAP_SAND).select("b0")

    # USGS empirical relationship: Sy = 0.042 + 0.0023 * sand(%)
    # Clamp Sy to [0.02, 0.30] to avoid extreme outliers
    sy = sand_pct.multiply(0.0023).add(0.042).clamp(0.02, 0.30).rename("sy")

    _sy_image = sy
    return _sy_image


def get_gwd_image(year: int) -> ee.Image:
    """Computes Groundwater Depth Change (GWD) in meters for a given year.
    GWD = GWSA (cm) / (Sy × 100), where Sy is derived per-pixel from soil texture.
    Positive = water table rising, Negative = water table dropping.
    Returns a single-band ee.Image named 'gwd'."""
    gwsa = get_gwsa_image(year).resample('bilinear')
    sy = _get_specific_yield_map()
    # Convert cm anomaly to meters of water table change: GWSA(cm) / (Sy * 100)
    gwd = gwsa.divide(sy.multiply(100)).rename("gwd")
    return gwd


def get_boundary() -> ee.Geometry:
    # Merges all 12 custom local regions into a single unified country geometry for seamless satellite clipping
    return get_morocco_regions().union().geometry()


def get_recharge_image(year: int) -> ee.Image:
    """Computes Groundwater Recharge proxy in cm using GLDAS Water Balance:
    Recharge = Max(Precipitation - Evapotranspiration, 0) * 0.20
    Precipitation is 'Rainf_tavg' (kg/m2/s) accumulated over year (multiply by 3153600).
    Evapotranspiration is 'Evap_tavg' (kg/m2/s) accumulated over year (multiply by 3153600).
    """
    gldas = ee.ImageCollection(GLDAS_DATASET).select(["Rainf_tavg", "Evap_tavg"]).filterDate(f"{year}-01-01", f"{year + 1}-01-01").mean()
    precip = gldas.select("Rainf_tavg").multiply(3153600) # Convert kg/m2/s to cm/year
    evap = gldas.select("Evap_tavg").multiply(3153600)
    recharge = precip.subtract(evap).multiply(0.20).clamp(0, 100).rename("recharge")
    return recharge


def get_water_quantity_image(year: int) -> ee.Image:
    """Estimates surface water presence/quantity from Sentinel-2 NDWI:
    Quantity = Clamped NDWI [0, 0.5] scaled to [0, 1].
    """
    morocco_border = get_boundary()
    ndwi = (
        ee.ImageCollection(SENTINEL2_DATASET)
        .filterBounds(morocco_border)
        .filterDate(f"{year}-01-01", f"{year}-12-31")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
        .median()
        .normalizedDifference(["B3", "B8"])
    )
    quantity = ndwi.clamp(0, 0.5).divide(0.5).rename("water_quantity")
    return quantity


def get_suitability_image(year: int) -> ee.Image:
    """Computes Land Suitability Index (0 to 1) for agriculture:
    Suitability = 0.6 * NDVI + 0.4 * (NDWI + 0.2)
    """
    morocco_border = get_boundary()
    s2 = (
        ee.ImageCollection(SENTINEL2_DATASET)
        .filterBounds(morocco_border)
        .filterDate(f"{year}-01-01", f"{year}-12-31")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
        .median()
    )
    ndvi = s2.normalizedDifference(["B8", "B4"])
    ndwi = s2.normalizedDifference(["B3", "B8"])
    suitability = ndvi.multiply(0.6).add(ndwi.add(0.2).multiply(0.4)).clamp(0, 1).rename("suitability")
    return suitability

def admin2() -> str:
    # 1. Load the regions from our custom local FeatureCollection (already includes all 12 regions)
    morocco_regions = get_morocco_regions().filter(
        ee.Filter.inList("shapeGroup", ["MAR", "ESH"])
    )
    
    # 2. Paint outlines onto a transparent image (so only borders are drawn, no solid fill)
    empty = ee.Image().byte()
    outlines = empty.paint(
        featureCollection=morocco_regions,
        color=1,
        width=2
    )
    
    # 3. Get GEE map ID for the outline image (using a clean dark-grey outline)
    map_id = outlines.getMapId({"palette": ["#334155"], "min": 1, "max": 1})
    
    return map_id["tile_fetcher"].url_format


def list_regions_morocco() -> list:
    # Fetches all 12 Moroccan admin regions from our custom local FeatureCollection, returns a sorted list of region names
    morocco = get_morocco_regions().filter(
        ee.Filter.eq("shapeGroup", "MAR")
    )
    regions = morocco.aggregate_array("shapeName").distinct().sort()
    return regions.getInfo()


def get_region(region_name: str) -> ee.Geometry:
    # Filters custom local regions for a single region by name, returns its geometry polygon
    morocco = get_morocco_regions().filter(
        ee.Filter.eq("shapeGroup", "MAR")
    )
    selected_region = morocco.filter(ee.Filter.eq("shapeName", region_name))
    return selected_region.geometry()


def gwsa_map(year: int) -> geemap.Map:
    # Computes true Groundwater Storage Anomaly (GWSA) for the given year, clips to Morocco
    morocco_border = get_boundary()
    ground_water = get_gwsa_image(year).resample('bilinear').clip(morocco_border)

    gw_vis = {
        "min": -2,
        "max": 4,
        "palette": ["#d73027", "#fc8d59", "#fee090", "#e0f3f8", "#91bfdb", "#4575b4"],
    }

    Map = geemap.Map()
    Map.centerObject(morocco_border, 5)
    Map.addLayer(ground_water, gw_vis, f"Groundwater Storage Anomaly {year}")
    Map.add_colorbar(
        vis_params=gw_vis,
        label="Groundwater Storage Anomaly (cm)",
        layer_name="GW_Colorbar",
        orientation="horizontal",
        transparent_bg=True,
    )

    return Map


def gwd_map(year: int) -> geemap.Map:
    # Computes Groundwater Depth Change (GWD) in meters for a given year, clips to Morocco
    morocco_border = get_boundary()
    gwd = get_gwd_image(year).clip(morocco_border)

    gwd_vis = {
        "min": -2,
        "max": 2,
        "palette": ["#d73027", "#fc8d59", "#fee090", "#e0f3f8", "#91bfdb", "#4575b4"],
    }

    Map = geemap.Map()
    Map.centerObject(morocco_border, 5)
    Map.addLayer(gwd, gwd_vis, f"Groundwater Depth Change {year}")
    Map.add_colorbar(
        vis_params=gwd_vis,
        label="Groundwater Depth Change (m)",
        layer_name="GWD_Colorbar",
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


def gwsa_data(year: int, region: ee.Geometry) -> dict:
    # Computes true GWSA for the year, returns spatial mean (cm) inside the given region as dict
    gwsa = get_gwsa_image(year)

    data = gwsa.reduceRegion(
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


def gwd_data(year: int, region: ee.Geometry) -> dict:
    # Computes Groundwater Depth Change (GWD) in meters for a given year, returns spatial mean inside the given region as dict
    gwd = get_gwd_image(year)

    data = gwd.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=55000,
        maxPixels=1e9,
    )
    return data.getInfo()


def get_all_regions_data(year: int, index: str) -> dict:
    # Computes spatial mean index values for all 12 Moroccan regions at once using reduceRegions to minimize GEE calls
    # Check cache first
    cache_key = f"{index}_{year}"
    if cache_key in _regions_cache:
        return _regions_cache[cache_key]

    regions = get_morocco_regions().filter(ee.Filter.eq("shapeGroup", "MAR"))
    index_lower = index.lower()
    if index_lower == "gwsa":
        image = get_gwsa_image(year)
        band_name = "gwsa"
        scale = 55000
    elif index_lower == "gwd":
        image = get_gwd_image(year)
        band_name = "gwd"
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
    elif index_lower in ["recharge", "groundwater recharge"]:
        image = get_recharge_image(year)
        band_name = "recharge"
        scale = 55000
    elif index_lower in ["water_quantity", "water quantity", "surface water quantity"]:
        image = get_water_quantity_image(year)
        band_name = "water_quantity"
        scale = 10000
    elif index_lower in ["suitability", "land suitability"]:
        image = get_suitability_image(year)
        band_name = "suitability"
        scale = 10000
    else:
        raise ValueError(f"Invalid index '{index}'. Use 'gwsa', 'gwd', 'ndwi', 'ndvi', 'recharge', 'water_quantity', or 'suitability'.")

    try:
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
    except Exception as e:
        print(f"Error computing all regions data for {index} in {year}: {e}")
        result = {}

    # Save to cache
    _regions_cache[cache_key] = result
    return result


def get_time_series(region_name: str, index: str, start_year: int, end_year: int) -> dict:
    # Computes a yearly time series server-side in one batched GEE call instead of looping year by year
    region_geom = get_region(region_name)
    index_lower = index.lower()
    years = list(range(start_year, end_year + 1))
    ee_years = ee.List(years)

    if index_lower in ["gwsa", "grace"]:
        def compute_year_gw(y):
            y = ee.Number(y)
            start = ee.Date.fromYMD(y, 1, 1)
            end = ee.Date.fromYMD(y, 12, 31)
            # GRACE TWSA
            grace_twsa = (
                ee.ImageCollection(GRACE_DATASET)
                .select("lwe_thickness")
                .filterDate(start, end)
                .mean()
            )
            # GLDAS surface storage for this year
            gldas_year = (
                ee.ImageCollection(GLDAS_DATASET)
                .select(_GLDAS_BANDS)
                .filterDate(start, end)
                .mean()
            ).reduce(ee.Reducer.sum()).divide(10).rename("surface_storage")
            gldas_anomaly = gldas_year.subtract(_get_gldas_baseline())
            gwsa = grace_twsa.subtract(gldas_anomaly).rename("gwsa")
            val = gwsa.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region_geom,
                scale=55000,
                maxPixels=1e9,
                bestEffort=True,
            ).get("gwsa")
            return ee.Feature(None, {"year": y, "value": val})

        results = ee.FeatureCollection(ee_years.map(compute_year_gw))

    elif index_lower in ["gwd", "groundwater depth"]:
        def compute_year_gwd(y):
            y = ee.Number(y)
            start = ee.Date.fromYMD(y, 1, 1)
            end = ee.Date.fromYMD(y, 12, 31)
            # GRACE TWSA
            grace_twsa = (
                ee.ImageCollection(GRACE_DATASET)
                .select("lwe_thickness")
                .filterDate(start, end)
                .mean()
            )
            # GLDAS surface storage for this year
            gldas_year = (
                ee.ImageCollection(GLDAS_DATASET)
                .select(_GLDAS_BANDS)
                .filterDate(start, end)
                .mean()
            ).reduce(ee.Reducer.sum()).divide(10).rename("surface_storage")
            gldas_anomaly = gldas_year.subtract(_get_gldas_baseline())
            gwsa = grace_twsa.subtract(gldas_anomaly).rename("gwsa")
            sy = _get_specific_yield_map()
            gwd = gwsa.divide(sy.multiply(100)).rename("gwd")
            val = gwd.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region_geom,
                scale=55000,
                maxPixels=1e9,
                bestEffort=True,
            ).get("gwd")
            return ee.Feature(None, {"year": y, "value": val})

        results = ee.FeatureCollection(ee_years.map(compute_year_gwd))

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

    elif index_lower in ["recharge", "groundwater recharge"]:
        def compute_year_recharge(y):
            y = ee.Number(y)
            start = ee.Date.fromYMD(y, 1, 1)
            end = ee.Date.fromYMD(y, 12, 31)
            gldas = ee.ImageCollection(GLDAS_DATASET).select(["Rainf_tavg", "Evap_tavg"]).filterDate(start, end).mean()
            precip = gldas.select("Rainf_tavg").multiply(3153600)
            evap = gldas.select("Evap_tavg").multiply(3153600)
            recharge = precip.subtract(evap).multiply(0.20).clamp(0, 100).rename("recharge")
            val = recharge.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region_geom,
                scale=55000,
                maxPixels=1e9,
                bestEffort=True,
            ).get("recharge")
            return ee.Feature(None, {"year": y, "value": val})
        results = ee.FeatureCollection(ee_years.map(compute_year_recharge))

    elif index_lower in ["water_quantity", "water quantity", "surface water quantity"]:
        def compute_year_water_quantity(y):
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
            quantity = img.clamp(0, 0.5).divide(0.5).rename("water_quantity")
            val = quantity.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region_geom,
                scale=10000,
                maxPixels=1e9,
                bestEffort=True,
            ).get("water_quantity")
            return ee.Feature(None, {"year": y, "value": val})
        results = ee.FeatureCollection(ee_years.map(compute_year_water_quantity))

    elif index_lower in ["suitability", "land suitability"]:
        def compute_year_suitability(y):
            y = ee.Number(y)
            start = ee.Date.fromYMD(y, 1, 1)
            end = ee.Date.fromYMD(y, 12, 31)
            s2 = (
                ee.ImageCollection(SENTINEL2_DATASET)
                .filterBounds(region_geom)
                .filterDate(start, end)
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
                .median()
            )
            ndvi = s2.normalizedDifference(["B8", "B4"])
            ndwi = s2.normalizedDifference(["B3", "B8"])
            suitability = ndvi.multiply(0.6).add(ndwi.add(0.2).multiply(0.4)).clamp(0, 1).rename("suitability")
            val = suitability.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region_geom,
                scale=10000,
                maxPixels=1e9,
                bestEffort=True,
            ).get("suitability")
            return ee.Feature(None, {"year": y, "value": val})
        results = ee.FeatureCollection(ee_years.map(compute_year_suitability))

    else:
        raise ValueError(f"Invalid index '{index}'. Use 'gwsa', 'gwd', 'ndwi', 'ndvi', 'recharge', 'water_quantity', or 'suitability'.")

    features = results.getInfo().get("features", [])
    return {
        int(f["properties"]["year"]): f["properties"].get("value")
        for f in features
    }


def get_tile_url(year: int, index: str) -> str:
    # Generates a map tile URL for the specified index and year, allowing the frontend to overlay the satellite layer on a map
    index_lower = index.lower()
    cache_key = f"{index_lower}_{year}"
    if cache_key in _tile_url_cache:
        return _tile_url_cache[cache_key]

    morocco_border = get_boundary()
    
    if index_lower in ["gwsa"]:
        image = get_gwsa_image(year).resample('bilinear').clip(morocco_border)
        vis_params = {
            "min": -2,
            "max": 4,
            "palette": ["#d73027", "#fc8d59", "#fee090", "#e0f3f8", "#91bfdb", "#4575b4"],
        }
    elif index_lower in ["surface water", "ndwi"]:
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
    elif index_lower in ["land use", "ndvi"]:
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
    elif index_lower in ["gwd", "groundwater depth"]:
        image = get_gwd_image(year).clip(morocco_border)
        vis_params = {
            "min": -2,
            "max": 2,
            "palette": ["#d73027", "#fc8d59", "#fee090", "#e0f3f8", "#91bfdb", "#4575b4"],
        }
    elif index_lower in ["recharge", "groundwater recharge"]:
        image = get_recharge_image(year).clip(morocco_border)
        vis_params = {
            "min": 0,
            "max": 25,
            "palette": ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#084594"],
        }
    elif index_lower in ["water quantity", "water_quantity", "surface water quantity"]:
        image = get_water_quantity_image(year).clip(morocco_border)
        vis_params = {
            "min": 0,
            "max": 1,
            "palette": ["#f7fcf0", "#e0f3db", "#ccebc5", "#a8ddb5", "#7bccc4", "#4eb3d3", "#2b8cbe", "#08589e"],
        }
    elif index_lower in ["suitability", "land suitability"]:
        image = get_suitability_image(year).clip(morocco_border)
        vis_params = {
            "min": 0,
            "max": 0.8,
            "palette": ["#f7fc74", "#dbf374", "#c5eb74", "#a5dd74", "#74cc74", "#4eb374", "#2bbe74", "#056201"],
        }
    else:
        raise ValueError(f"Invalid index '{index}'. Use 'gwsa', 'gwd', 'surface water' (ndwi), 'land use' (ndvi), 'recharge', 'water quantity', or 'suitability'.")
        
    map_id = image.getMapId(vis_params)
    tile_url = map_id["tile_fetcher"].url_format
    _tile_url_cache[cache_key] = tile_url
    return tile_url

def get_point_data(lat: float, lon: float, year: int) -> dict:
    """
    Queries Earth Engine at a single coordinate using appropriate buffers in parallel.
    - Groundwater (GRACE): 25km buffer due to low satellite resolution.
    - NDWI and NDVI (Sentinel-2): 100m buffer for high spatial precision.
    """
    point = ee.Geometry.Point([lon, lat])
    
    def fetch_gwsa():
        try:
            gwsa = get_gwsa_image(year)
            return gwsa.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point.buffer(25000),
                scale=25000
            ).get("gwsa").getInfo()
        except Exception as e:
            print(f"EE Point GW error: {e}")
            return None

    def fetch_gwd():
        try:
            gwd = get_gwd_image(year)
            return gwd.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point.buffer(25000),
                scale=25000
            ).get("gwd").getInfo()
        except Exception as e:
            print(f"EE Point GWD error: {e}")
            return None

    def fetch_ndwi():
        try:
            ndwi_img = (
                ee.ImageCollection(SENTINEL2_DATASET)
                .filterBounds(point.buffer(100))
                .filterDate(f"{year}-01-01", f"{year}-12-31")
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
                .median()
                .normalizedDifference(["B3", "B8"])
            )
            return ndwi_img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point.buffer(100),
                scale=10,
                bestEffort=True
            ).get("nd").getInfo()
        except Exception as e:
            print(f"EE Point NDWI error: {e}")
            return None

    def fetch_ndvi():
        try:
            ndvi_img = (
                ee.ImageCollection(SENTINEL2_DATASET)
                .filterBounds(point.buffer(100))
                .filterDate(f"{year}-01-01", f"{year}-12-31")
                .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", MAX_CLOUD_PERCENT))
                .median()
                .normalizedDifference(["B8", "B4"])
            )
            return ndvi_img.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point.buffer(100),
                scale=10,
                bestEffort=True
            ).get("nd").getInfo()
        except Exception as e:
            print(f"EE Point NDVI error: {e}")
            return None

    def fetch_recharge():
        try:
            recharge = get_recharge_image(year)
            return recharge.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point.buffer(25000),
                scale=25000
            ).get("recharge").getInfo()
        except Exception as e:
            print(f"EE Point recharge error: {e}")
            return None

    def fetch_water_quantity():
        try:
            quantity = get_water_quantity_image(year)
            return quantity.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point.buffer(100),
                scale=10,
                bestEffort=True
            ).get("water_quantity").getInfo()
        except Exception as e:
            print(f"EE Point water quantity error: {e}")
            return None

    def fetch_suitability():
        try:
            suitability = get_suitability_image(year)
            return suitability.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=point.buffer(100),
                scale=10,
                bestEffort=True
            ).get("suitability").getInfo()
        except Exception as e:
            print(f"EE Point suitability error: {e}")
            return None

    with ThreadPoolExecutor(max_workers=7) as executor:
        f_gwsa = executor.submit(fetch_gwsa)
        f_gwd = executor.submit(fetch_gwd)
        f_ndwi = executor.submit(fetch_ndwi)
        f_ndvi = executor.submit(fetch_ndvi)
        f_recharge = executor.submit(fetch_recharge)
        f_water_quantity = executor.submit(fetch_water_quantity)
        f_suitability = executor.submit(fetch_suitability)
        
        gw_val = f_gwsa.result()
        gwd_val = f_gwd.result()
        ndwi_val = f_ndwi.result()
        ndvi_val = f_ndvi.result()
        recharge_val = f_recharge.result()
        water_quantity_val = f_water_quantity.result()
        suitability_val = f_suitability.result()

    return {
        "lat": lat,
        "lon": lon,
        "year": year,
        "gwsa": gw_val,
        "gwd": gwd_val,
        "ndwi": ndwi_val,
        "ndvi": ndvi_val,
        "recharge": recharge_val,
        "water_quantity": water_quantity_val,
        "suitability": suitability_val
    }


