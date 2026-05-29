


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

