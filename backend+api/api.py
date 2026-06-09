from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import backend
import chat_advisor

class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []
    current_year: Optional[int] = 2024
    current_index: Optional[str] = None
    current_region: Optional[str] = None
    current_location: Optional[dict] = None


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
    
    - **index**: 'gwsa', 'ndwi', or 'ndvi'
    - **year**: e.g. 2020
    """
    index_lower = index.lower()
    if index_lower in ["gwsa", "gwd", "grace"] and (year < 2002 or year > 2024):
        raise HTTPException(status_code=400, detail=f"GRACE Groundwater Storage Anomaly data is only available from 2002 to 2024. Received year={year}.")
    if index_lower in ["surface water", "ndwi", "land use", "ndvi"] and (year < 2017 or year > 2024):
        raise HTTPException(status_code=400, detail=f"Sentinel-2 data ({index}) is only available from 2017 to 2024. Received year={year}.")
    try:
        tile_url = backend.get_tile_url(year, index)
        return {"index": index, "year": year, "tile_url": tile_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Single region data ───────────────────────────────────────────────────────

@app.get("/data/gwsa/{year}")
def get_gwsa_data(year: int, region: str = Query(..., description="Region name")):
    """Returns mean Groundwater Storage Anomaly (cm) for a region and year."""
    try:
        region_geom = backend.get_region(region)
        data = backend.gwsa_data(year, region_geom)
        return {"region": region, "year": year, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/gwd/{year}")
def get_gwd_data(year: int, region: str = Query(..., description="Region name")):
    """Returns mean Groundwater Depth Change (m) for a region and year."""
    try:
        region_geom = backend.get_region(region)
        data = backend.gwd_data(year, region_geom)
        return {"region": region, "year": year, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/ndwi/{year}")
def get_ndwi_data(year: int, region: str = Query(..., description="Region name")):
    """Returns mean NDWI value for a region and year."""
    try:
        region_geom = backend.get_region(region)
        data = backend.ndwi_data(year, region_geom)
        return {"region": region, "year": year, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/data/ndvi/{year}")
def get_ndvi_data(year: int, region: str = Query(..., description="Region name")):
    """Returns mean NDVI value for a region and year."""
    try:
        region_geom = backend.get_region(region)
        data = backend.ndvi_data(year, region_geom)
        return {"region": region, "year": year, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── All regions at once ──────────────────────────────────────────────────────

@app.get("/data/all-regions/{index}/{year}")
def get_all_regions(index: str, year: int):
    """
    Returns mean index value for all 12 Moroccan regions in one call.
    
    - **index**: 'gwsa', 'ndwi', or 'ndvi'
    - **year**: e.g. 2020
    """
    index_lower = index.lower()
    if index_lower in ["gwsa", "gwd", "grace"] and (year < 2002 or year > 2024):
        raise HTTPException(status_code=400, detail=f"GRACE Groundwater Storage Anomaly data is only available from 2002 to 2024. Received year={year}.")
    if index_lower in ["ndwi", "ndvi"] and (year < 2017 or year > 2024):
        raise HTTPException(status_code=400, detail=f"Sentinel-2 data ({index}) is only available from 2017 to 2024. Received year={year}.")
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

@app.get("/admin2")
def get_admin2():
    """Returns the GEE tile URL for the administrative regions of Morocco."""
    try:
        tile_url = backend.admin2()
        return {"tile_url": tile_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat")
def chat_query(request: ChatRequest):
    """
    Processes user query about Moroccan indices and investment,
    integrates map context, and returns data-driven analysis.
    """
    try:
        response_text = chat_advisor.generate_chat_response(
            message=request.message,
            history=[{"role": m.role, "content": m.content} for m in request.history],
            year=request.current_year or 2024,
            current_index=request.current_index,
            current_region=request.current_region,
            current_location=request.current_location
        )
        return {"response": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/point")
def get_point_data(lat: float = Query(..., description="Latitude"), lon: float = Query(..., description="Longitude"), year: int = Query(..., description="Year")):
    """Returns Groundwater, NDWI, and NDVI values for a specific coordinate point and year."""
    if year < 2002 or year > 2024:
        raise HTTPException(status_code=400, detail=f"Data is only available from 2002 to 2024. Received year={year}.")
    try:
        data = backend.get_point_data(lat, lon, year)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
