const API_BASE = "http://localhost:8000";

// In-memory caching dictionaries for platform data
const tileUrlCache = {};
const regionsDataCache = {};

export async function getRegions() {
    // returns an array of region objects
    const response = await fetch(`${API_BASE}/regions`);

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return data.regions;
}

export async function getAllRegionsData(index, year) {
    const cacheKey = `${index.toLowerCase()}_${year}`;
    if (regionsDataCache[cacheKey]) {
        return regionsDataCache[cacheKey];
    }

    const response = await fetch(`${API_BASE}/data/all-regions/${index}/${year}`);

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    regionsDataCache[cacheKey] = data.regions;
    return data.regions;
}

export async function getTileUrl(index, year) {
    const cacheKey = `${index}_${year}`;
    if (tileUrlCache[cacheKey]) {
        return tileUrlCache[cacheKey];
    }

    const response = await fetch(`${API_BASE}/tile/${index}/${year}`);

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    tileUrlCache[cacheKey] = data.tile_url;
    return data.tile_url;
}

export async function getTimeSeries(region, index, startYear, endYear) {
    const params = new URLSearchParams({
        region: region,
        index: index,
        start_year: startYear,
        end_year: endYear,
    });

    const response = await fetch(`${API_BASE}/data/time-series?${params}`);

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return data.series;
}

export async function getAdmin2TileUrl() {
    const response = await fetch(`${API_BASE}/admin2`);

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return data.tile_url;
}

export async function postChatQuery(message, history = [], context = {}) {
    const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            message: message,
            history: history,
            current_year: context.year ? parseInt(context.year) : 2024,
            current_index: context.index,
            current_region: context.region,
            current_location: context.location
        })
    });

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return data.response;
}

export async function getPointData(lat, lon, year) {
    const params = new URLSearchParams({
        lat: lat,
        lon: lon,
        year: year
    });

    const response = await fetch(`${API_BASE}/data/point?${params}`);

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    return await response.json();
}

// Background preloader routine to cache all platform GEE data (years 2017 to 2024)
export function preloadAllPlatformData(onProgress) {
    const years = [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024];
    const tileIndices = ['GWSA', 'GWD', 'Surface Water', 'Land Use'];
    const regionIndices = ['gwsa', 'gwd', 'ndwi', 'ndvi'];
    
    let completedTasks = 0;
    const totalTasks = years.length * (tileIndices.length + regionIndices.length);

    async function startPreload() {
        console.log("🚀 Preloading Morocco GEE indices and regional data in the background...");
        
        // Sequentially preload by year to avoid hammering the local FastAPI backend with concurrent requests
        for (const year of years) {
            try {
                await Promise.all([
                    ...tileIndices.map(index => getTileUrl(index, year).catch(() => null)),
                    ...regionIndices.map(index => getAllRegionsData(index, year).catch(() => null))
                ]);
                completedTasks += tileIndices.length + regionIndices.length;
                const progress = Math.round((completedTasks / totalTasks) * 100);
                if (onProgress) {
                    onProgress(progress);
                }
            } catch (err) {
                console.error(`⚠️ Failed to preload GEE data for year ${year}:`, err);
            }
        }
        console.log("⚡ Morocco GEE background preloading completed! Local cache is fully warmed.");
    }

    startPreload();
}
