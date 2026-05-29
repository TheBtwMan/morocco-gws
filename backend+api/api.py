from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import backend

app = FastAPI(
    title="Geo AI Morocco",
    description="API for geospatial analysis of Morocco using Google Earth Engine",
    version="1.0.0",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Regions ──────────────────────────────────────────────────────────────────

@app.get("/regions")
def get_regions():
    """Returns all 12 Moroccan admin regions."""
    try:
        regions = backend.list_regions_morocco()
        return {"regions": regions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Tile URLs (for map overlays) ─────────────────────────────────────────────

@app.get("/tile/{index}/{year}")
def get_tile(index: str, year: int):
    """
    Returns a tile URL for a given index and year.
    
    - **index**: 'groundwater', 'ndwi', or 'ndvi'
    - **year**: e.g. 2020
    """
    try:
        tile_url = backend.get_tile_url(year, index)
        return {"index": index, "year": year, "tile_url": tile_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Single region data ───────────────────────────────────────────────────────

@app.get("/data/groundwater/{year}")
def get_groundwater_data(year: int, region: str = Query(..., description="Region name")):
    """Returns mean groundwater anomaly (cm) for a region and year."""
    try:
        data = backend.groundwater_data(year, region)
        return {"region": region, "year": year, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/ndwi/{year}")
def get_ndwi_data(year: int, region: str = Query(..., description="Region name")):
    """Returns mean NDWI value for a region and year."""
    try:
        data = backend.ndwi_data(year, region)
        return {"region": region, "year": year, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/ndvi/{year}")
def get_ndvi_data(year: int, region: str = Query(..., description="Region name")):
    """Returns mean NDVI value for a region and year."""
    try:
        data = backend.ndvi_data(year, region)
        return {"region": region, "year": year, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── All regions at once ──────────────────────────────────────────────────────

@app.get("/data/all-regions/{index}/{year}")
def get_all_regions(index: str, year: int):
    """
    Returns mean index value for all 12 Moroccan regions in one call.
    
    - **index**: 'groundwater', 'ndwi', or 'ndvi'
    - **year**: e.g. 2020
    """
    try:
        data = backend.get_all_regions_data(year, index)
        return {"index": index, "year": year, "regions": data}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Time series ──────────────────────────────────────────────────────────────

@app.get("/data/time-series")
def get_time_series(
    region: str = Query(..., description="Region name"),
    index: str = Query(..., description="'groundwater', 'ndwi', or 'ndvi'"),
    start_year: int = Query(..., description="Start year"),
    end_year: int = Query(..., description="End year"),
):
    """
    Returns yearly index values for a region over a range of years.
    Useful for building charts and trend analysis.
    """
    if start_year > end_year:
        raise HTTPException(status_code=400, detail="start_year must be <= end_year")
    try:
        data = backend.get_time_series(region, index, start_year, end_year)
        return {
            "region": region,
            "index": index,
            "start_year": start_year,
            "end_year": end_year,
            "series": data,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

