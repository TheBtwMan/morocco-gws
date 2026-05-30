


const API_BASE = "http://localhost:8000";


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
    const response = await fetch(`${API_BASE}/data/all-regions/${index}/${year}`);

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    return data.regions;
}


export async function getTileUrl(index, year) {
    const response = await fetch(`${API_BASE}/tile/${index}/${year}`);

    if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
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
            current_region: context.region
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





