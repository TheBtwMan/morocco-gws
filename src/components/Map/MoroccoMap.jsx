import React, { useState, useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getTileUrl, getAllRegionsData, getPointData } from '../../services/apii';
import regionsGeoJSON from '../../data/ma_simplified.json';

const COMMUNE_COORDINATES = [
  { name: "Marrakech", lat: 31.6295, lon: -7.9811 },
  { name: "Agadir", lat: 30.4278, lon: -9.5981 },
  { name: "Casablanca", lat: 33.5731, lon: -7.5898 },
  { name: "Rabat", lat: 34.0209, lon: -6.8416 },
  { name: "Fès", lat: 34.0331, lon: -5.0003 },
  { name: "Tanger", lat: 35.7595, lon: -5.8340 },
  { name: "Oujda", lat: 34.6867, lon: -1.9114 },
  { name: "Nador", lat: 35.1681, lon: -2.9335 },
  { name: "Kénitra", lat: 34.2540, lon: -6.5890 },
  { name: "Tétouan", lat: 35.5889, lon: -5.3626 },
  { name: "Safi", lat: 32.2994, lon: -9.2372 },
  { name: "El Jadida", lat: 33.2316, lon: -8.5007 },
  { name: "Béni Mellal", lat: 32.3394, lon: -6.3608 },
  { name: "Khouribga", lat: 32.8807, lon: -6.9063 },
  { name: "Settat", lat: 33.0010, lon: -7.6166 },
  { name: "Taza", lat: 34.2189, lon: -4.0100 },
  { name: "Meknès", lat: 33.8938, lon: -5.5473 },
  { name: "Mohammedia", lat: 33.6835, lon: -7.3849 },
  { name: "Guelmim", lat: 28.9864, lon: -10.0574 },
  { name: "Dakhla", lat: 23.6848, lon: -15.9580 },
  { name: "Laâyoune", lat: 27.1500, lon: -13.2000 },
  { name: "Taroudant", lat: 30.4703, lon: -8.8770 },
  { name: "Ouarzazate", lat: 30.9189, lon: -6.8934 },
  { name: "Errachidia", lat: 31.9317, lon: -4.4244 },
  { name: "Tiznit", lat: 29.6975, lon: -9.7317 },
  { name: "Essaouira", lat: 31.5085, lon: -9.7595 },
  { name: "Al Hoceïma", lat: 35.2472, lon: -3.9311 },
  { name: "Larache", lat: 35.1932, lon: -6.1550 },
  { name: "Ksar El Kebir", lat: 35.0022, lon: -5.9053 },
  { name: "Khemisset", lat: 33.8242, lon: -6.0664 },
  { name: "Berkane", lat: 34.9200, lon: -2.3200 },
  { name: "Taourirt", lat: 34.4072, lon: -2.8973 },
  { name: "Fquih Ben Salah", lat: 32.5083, lon: -6.6917 },
  { name: "Sidi Slimane", lat: 34.2600, lon: -6.0800 },
  { name: "Sidi Kacem", lat: 34.2200, lon: -5.7000 },
  { name: "Khenifra", lat: 32.9394, lon: -5.6678 },
  { name: "Youssoufia", lat: 32.2464, lon: -8.5294 },
  { name: "Benguerir", lat: 32.2300, lon: -7.9500 },
  { name: "Tan-Tan", lat: 28.4379, lon: -11.1025 },
  { name: "Smara", lat: 26.7384, lon: -11.6719 }
];

function SpatialInspectorCard({ inspector, onClose }) {
  if (!inspector) return null;

  const { title, lat, lon, loading, data, error } = inspector;

  const getSuitabilityAnalysis = () => {
    if (!data) return { title: "N/A", desc: "No indices loaded." };

    let totalScore = 0;
    if (data.suitability !== null && data.suitability !== undefined) {
      // Scale GEE LSI [0, 0.8] to [0, 100]
      totalScore = Math.min(Math.max((data.suitability / 0.8) * 100, 0), 100);
    } else {
      const { gwsa, ndwi, ndvi } = data;
      const gw = gwsa !== null ? gwsa : -0.5;
      const water = ndwi !== null ? ndwi : -0.1;
      const veg = ndvi !== null ? ndvi : 0.25;

      const gw_score = Math.min(Math.max((gw + 1.5) / 3 * 100, 0), 100);
      const water_score = Math.min(Math.max((water + 0.5) * 100, 0), 100);
      const veg_score = Math.min(Math.max(veg / 0.8 * 100, 0), 100);
      totalScore = Math.round(0.35 * gw_score + 0.3 * water_score + 0.35 * veg_score);
    }

    if (totalScore < 35) {
      return {
        title: "🔴 High Resource Risk",
        desc: "Significant groundwater storage depletion and low moisture indices. Unfavorable for water-intensive farming. Highly viable for solar installations."
      };
    } else if (totalScore < 60) {
      return {
        title: "🟡 Moderate Adaptive Outlook",
        desc: "Moderate vegetation and water cover. Good viability for drought-resistant trees (Olive, Argan) with automated drip irrigation."
      };
    } else {
      return {
        title: "🟢 High Viability",
        desc: "Favorable vegetation indexes and water metrics. Suitable for organic farming, active crop production, and agro-industries."
      };
    }
  };

  const suitability = getSuitabilityAnalysis();

  return (
    <div className="spatial-inspector-card">
      <div className="spatial-inspector-header">
        <h4>🔍 {title}</h4>
        <button className="spatial-inspector-close" onClick={onClose}>×</button>
      </div>

      <div className="spatial-inspector-body">
        <div className="inspector-coordinate-row">
          <span>Lat: {lat}</span>
          <span>Lon: {lon}</span>
        </div>

        {loading ? (
          <div className="spatial-inspector-loading">
            <div className="spatial-inspector-spinner"></div>
            <span>Querying Google Earth Engine...</span>
          </div>
        ) : error ? (
          <div style={{ color: '#ef4444', fontSize: '11px', padding: '10px 0', textAlign: 'center' }}>
            {error}
          </div>
        ) : (
          <>
            <div className="inspector-index-list">
              <div className="inspector-index-item">
                <span className="inspector-index-label">💧 Groundwater Storage Anomaly (GRACE)</span>
                <span className="inspector-index-value" style={{
                  color: data.gwsa === null ? '#94a3b8' : data.gwsa < -0.8 ? '#f87171' : data.gwsa < 0 ? '#fbbf24' : '#34d399'
                }}>
                  {data.gwsa !== null ? `${data.gwsa.toFixed(3)} cm` : 'No Data'}
                </span>
              </div>

              {data.gwd !== undefined && (
                <div className="inspector-index-item">
                  <span className="inspector-index-label">🕳️ Groundwater Depth Change (GWD)</span>
                  <span className="inspector-index-value" style={{
                    color: data.gwd === null ? '#94a3b8' : data.gwd < -0.4 ? '#f87171' : data.gwd < 0 ? '#fbbf24' : '#34d399'
                  }}>
                    {data.gwd !== null ? `${data.gwd.toFixed(3)} m` : 'No Data'}
                  </span>
                </div>
              )}

              {data.recharge !== undefined && (
                <div className="inspector-index-item">
                  <span className="inspector-index-label">🌧️ Groundwater Recharge (GWR)</span>
                  <span className="inspector-index-value" style={{
                    color: data.recharge === null ? '#94a3b8' : data.recharge < 2.0 ? '#f87171' : data.recharge < 10.0 ? '#fbbf24' : '#34d399'
                  }}>
                    {data.recharge !== null ? `${data.recharge.toFixed(3)} cm` : 'No Data'}
                  </span>
                </div>
              )}

              <div className="inspector-index-item">
                <span className="inspector-index-label">🌊 Surface Water (NDWI)</span>
                <span className="inspector-index-value" style={{
                  color: data.ndwi === null ? '#94a3b8' : data.ndwi < -0.2 ? '#f87171' : data.ndwi < 0.15 ? '#fbbf24' : '#34d399'
                }}>
                  {data.ndwi !== null ? data.ndwi.toFixed(3) : 'No Data'}
                </span>
              </div>

              {data.water_quantity !== undefined && (
                <div className="inspector-index-item">
                  <span className="inspector-index-label">💧 Surface Water Quantity (SWQ)</span>
                  <span className="inspector-index-value" style={{
                    color: data.water_quantity === null ? '#94a3b8' : data.water_quantity < 0.15 ? '#f87171' : data.water_quantity < 0.4 ? '#fbbf24' : '#34d399'
                  }}>
                    {data.water_quantity !== null ? data.water_quantity.toFixed(3) : 'No Data'}
                  </span>
                </div>
              )}

              <div className="inspector-index-item">
                <span className="inspector-index-label">🌾 Land Use (NDVI)</span>
                <span className="inspector-index-value" style={{
                  color: data.ndvi === null ? '#94a3b8' : data.ndvi < 0.15 ? '#f87171' : data.ndvi < 0.4 ? '#fbbf24' : '#34d399'
                }}>
                  {data.ndvi !== null ? data.ndvi.toFixed(3) : 'No Data'}
                </span>
              </div>

              {data.suitability !== undefined && (
                <div className="inspector-index-item">
                  <span className="inspector-index-label">🚜 Land Suitability Index (LSI)</span>
                  <span className="inspector-index-value" style={{
                    color: data.suitability === null ? '#94a3b8' : data.suitability < 0.35 ? '#f87171' : data.suitability < 0.6 ? '#fbbf24' : '#34d399'
                  }}>
                    {data.suitability !== null ? data.suitability.toFixed(3) : 'No Data'}
                  </span>
                </div>
              )}
            </div>

            <div className="inspector-suitability">
              <div className="inspector-suitability-title">{suitability.title}</div>
              <div className="inspector-suitability-desc">{suitability.desc}</div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function MoroccoMap({ selectedYear, activeFilter, adminLevel, inspector, onInspect }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const regionsLayerRef = useRef(null);
  const satelliteLayerRef = useRef(null);
  const activeMarkerRef = useRef(null);

  const adminLevelRef = useRef(adminLevel);
  const selectedYearRef = useRef(selectedYear);
  const activeFilterRef = useRef(activeFilter);

  useEffect(() => { adminLevelRef.current = adminLevel; }, [adminLevel]);
  useEffect(() => { selectedYearRef.current = selectedYear; }, [selectedYear]);
  useEffect(() => { activeFilterRef.current = activeFilter; }, [activeFilter]);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    const map = L.map(mapContainerRef.current, {
      center: [31.5, -7.5],
      zoom: 5.3,
      zoomControl: true,
      attributionControl: false
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19
    }).addTo(map);

    mapInstanceRef.current = map;

    // Attach map clicks for point and commune inspectors
    map.on('click', (e) => {
      const { lat, lng } = e.latlng;
      const currentLevel = adminLevelRef.current;

      if (currentLevel === 'admin0-all') {
        handlePointClick(lat, lng, `📍 Point Inspection`);
      } else if (currentLevel === 'admin1-communes') {
        const nearest = findNearestCommune(lat, lng);
        handlePointClick(lat, lng, `🏡 Commune: ${nearest.name}`);
      }
    });

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  const findNearestCommune = (lat, lon) => {
    let nearest = COMMUNE_COORDINATES[0];
    let minDist = Infinity;

    for (const item of COMMUNE_COORDINATES) {
      const dist = Math.pow(lat - item.lat, 2) + Math.pow(lon - item.lon, 2);
      if (dist < minDist) {
        minDist = dist;
        nearest = item;
      }
    }
    return nearest;
  };

  const updateMapMarker = (lat, lon) => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (activeMarkerRef.current) {
      map.removeLayer(activeMarkerRef.current);
    }

    const customIcon = L.divIcon({
      className: 'custom-active-marker',
      html: `<div style="
        width: 14px;
        height: 14px;
        background: #7BD4E9;
        border: 2.5px solid #1a1a22;
        border-radius: 50%;
        box-shadow: 0 0 10px #7BD4E9;
      "></div>`,
      iconSize: [14, 14],
      iconAnchor: [7, 7]
    });

    activeMarkerRef.current = L.marker([lat, lon], { icon: customIcon }).addTo(map);
  };

  const handlePointClick = async (lat, lon, label) => {
    onInspect({
      title: label || `Coordinate Inspection`,
      lat: lat.toFixed(4),
      lon: lon.toFixed(4),
      loading: true,
      data: null
    });
    updateMapMarker(lat, lon);

    try {
      const data = await getPointData(lat, lon, selectedYearRef.current);
      onInspect(prev => {
        if (!prev) return null;
        return {
          ...prev,
          loading: false,
          data: {
            gwsa: data.gwsa,
            gwd: data.gwd,
            ndwi: data.ndwi,
            ndvi: data.ndvi,
            recharge: data.recharge,
            water_quantity: data.water_quantity,
            suitability: data.suitability
          }
        };
      });
    } catch (err) {
      console.error(err);
      onInspect(prev => {
        if (!prev) return null;
        return {
          ...prev,
          loading: false,
          error: "Failed to load pixel data from Earth Engine."
        };
      });
    }
  };

  const handleRegionClick = async (regionName, clickLat, clickLon) => {
    onInspect({
      title: `🗺️ Region: ${regionName}`,
      lat: clickLat.toFixed(4),
      lon: clickLon.toFixed(4),
      loading: true,
      data: null
    });
    updateMapMarker(clickLat, clickLon);

    try {
      const [gwData, gwdData, ndwiData, ndviData, rechargeData, waterQtyData, suitabilityData] = await Promise.all([
        getAllRegionsData('gwsa', selectedYearRef.current).catch(() => ({})),
        getAllRegionsData('gwd', selectedYearRef.current).catch(() => ({})),
        getAllRegionsData('ndwi', selectedYearRef.current).catch(() => ({})),
        getAllRegionsData('ndvi', selectedYearRef.current).catch(() => ({})),
        getAllRegionsData('recharge', selectedYearRef.current).catch(() => ({})),
        getAllRegionsData('water_quantity', selectedYearRef.current).catch(() => ({})),
        getAllRegionsData('suitability', selectedYearRef.current).catch(() => ({}))
      ]);

      onInspect(prev => {
        if (!prev) return null;
        return {
          ...prev,
          loading: false,
          data: {
            gwsa: gwData[regionName] !== undefined ? gwData[regionName] : null,
            gwd: gwdData[regionName] !== undefined ? gwdData[regionName] : null,
            ndwi: ndwiData[regionName] !== undefined ? ndwiData[regionName] : null,
            ndvi: ndviData[regionName] !== undefined ? ndviData[regionName] : null,
            recharge: rechargeData[regionName] !== undefined ? rechargeData[regionName] : null,
            water_quantity: waterQtyData[regionName] !== undefined ? waterQtyData[regionName] : null,
            suitability: suitabilityData[regionName] !== undefined ? suitabilityData[regionName] : null
          }
        };
      });
    } catch (err) {
      console.error(err);
      onInspect(prev => {
        if (!prev) return null;
        return {
          ...prev,
          loading: false,
          error: "Failed to fetch region average indexes."
        };
      });
    }
  };

  const handleCloseInspector = () => {
    onInspect(null);
    const map = mapInstanceRef.current;
    if (map && activeMarkerRef.current) {
      map.removeLayer(activeMarkerRef.current);
      activeMarkerRef.current = null;
    }
  };

  // Handle active cursor classes depending on modes
  useEffect(() => {
    const container = mapContainerRef.current;
    if (!container) return;

    if (adminLevel === 'admin0-all' || adminLevel === 'admin1-communes' || adminLevel === 'admin2-regions') {
      container.classList.add('inspecting-cursor');
    } else {
      container.classList.remove('inspecting-cursor');
    }

    // Close inspector card when mode resets
    handleCloseInspector();
  }, [adminLevel]);

  // Handle dynamic loading of Admin2 Regions interactive vector layer
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (regionsLayerRef.current) {
      map.removeLayer(regionsLayerRef.current);
      regionsLayerRef.current = null;
    }

    if (adminLevel === 'admin2-regions') {
      const newLayer = L.geoJSON(regionsGeoJSON, {
        style: {
          color: '#334155',
          weight: 2,
          fillColor: '#7BD4E9',
          fillOpacity: 0
        },
        onEachFeature: (feature, layer) => {
          layer.on({
            mouseover: (e) => {
              const ly = e.target;
              ly.setStyle({
                fillOpacity: 0.12,
                weight: 2.5,
                color: '#7BD4E9'
              });
            },
            mouseout: (e) => {
              const ly = e.target;
              ly.setStyle({
                fillOpacity: 0,
                weight: 2,
                color: '#334155'
              });
            },
            click: (e) => {
              const rName = feature.properties.name;
              handleRegionClick(rName, e.latlng.lat, e.latlng.lng);
            }
          });
        }
      }).addTo(map);

      regionsLayerRef.current = newLayer;
    }
  }, [adminLevel, selectedYear]);

  // Handle dynamic loading of satellite index overlay layer
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (activeFilter && activeFilter !== 'Decision Making') {
      getTileUrl(activeFilter, selectedYear)
        .then((tileUrl) => {
          if (!mapInstanceRef.current) return;

          if (satelliteLayerRef.current) {
            mapInstanceRef.current.removeLayer(satelliteLayerRef.current);
          }

          const newLayer = L.tileLayer(tileUrl, {
            maxZoom: 19,
            opacity: 1
          }).addTo(mapInstanceRef.current);

          satelliteLayerRef.current = newLayer;

          // Put regions border outline back on top of satellite layer if active
          if (regionsLayerRef.current) {
            regionsLayerRef.current.bringToFront();
          }
        })
        .catch((err) => {
          console.error("Error loading GEE satellite tile layer:", err);
        });
    } else {
      if (satelliteLayerRef.current) {
        map.removeLayer(satelliteLayerRef.current);
        satelliteLayerRef.current = null;
      }
    }
  }, [activeFilter, selectedYear]);

  function MapLegend({ activeFilter }) {
    if (!activeFilter || activeFilter === 'Decision Making') return null;

    let legendItems = [];
    let title = "";

    if (activeFilter === 'GWSA') {
      title = "GWSA — Groundwater Storage Anomaly";
      legendItems = [
        { label: "High Surplus (+3.0 to +4.0 cm)", color: "#4575b4" },
        { label: "Moderate Surplus (+2.0 to +3.0 cm)", color: "#91bfdb" },
        { label: "Mild Surplus (+1.0 to +2.0 cm)", color: "#e0f3f8" },
        { label: "Normal / Stable (0.0 to +1.0 cm)", color: "#fee090" },
        { label: "Moderate Deficit (-1.0 to 0.0 cm)", color: "#fc8d59" },
        { label: "Severe Deficit (-2.0 to -1.0 cm)", color: "#d73027" },
      ];
    } else if (activeFilter === 'GWD') {
      title = "GWD — Groundwater Depth Change";
      legendItems = [
        { label: "High Rise (+1.3 to +2.0 m)", color: "#4575b4" },
        { label: "Moderate Rise (+0.6 to +1.3 m)", color: "#91bfdb" },
        { label: "Mild Rise (0.0 to +0.6 m)", color: "#e0f3f8" },
        { label: "Mild Drop (-0.6 to 0.0 m)", color: "#fee090" },
        { label: "Moderate Drop (-1.3 to -0.6 m)", color: "#fc8d59" },
        { label: "Severe Drop (-2.0 to -1.3 m)", color: "#d73027" },
      ];
    } else if (activeFilter === 'Surface Water') {
      title = "NDWI — Surface Water";
      legendItems = [
        { label: "Permanent Water (0.5)", color: "#0000CD" },
        { label: "Water Bodies (0.3)", color: "#1E90FF" },
        { label: "Shallow Water (0.1)", color: "#87CEEB" },
        { label: "Wet / Humid Soil (0.0)", color: "#FFFACD" },
        { label: "Dry Soil (-0.2)", color: "#D2691E" },
        { label: "Very Dry Soil (-0.5)", color: "#8B4513" },
      ];
    } else if (activeFilter === 'Land Use' || activeFilter === 'NDVI') {
      title = "NDVI — Land Use / Vegetation";
      legendItems = [
        { label: "Dense Forest (0.7+)", color: "#056201" },
        { label: "Moderate Vegetation (0.5)", color: "#74A901" },
        { label: "Sparse Vegetation (0.3)", color: "#FCD163" },
        { label: "Cropland / Agriculture (0.2)", color: "#99B718" },
        { label: "Bare Soil (0.1)", color: "#CE7E45" },
        { label: "No Vegetation (0.0)", color: "#FFFFFF" },
      ];
    } else if (activeFilter === 'Recharge') {
      title = "GWR — Groundwater Recharge";
      legendItems = [
        { label: "High Recharge (>20 cm/yr)", color: "#084594" },
        { label: "Moderate-High (15-20 cm/yr)", color: "#2171b5" },
        { label: "Moderate (10-15 cm/yr)", color: "#4292c6" },
        { label: "Low-Moderate (5-10 cm/yr)", color: "#6baed6" },
        { label: "Very Low (2-5 cm/yr)", color: "#9ecae1" },
        { label: "Deficit (0-2 cm/yr)", color: "#deebf7" },
        { label: "Minimal / None (0 cm/yr)", color: "#f7fbff" },
      ];
    } else if (activeFilter === 'Water Quantity') {
      title = "SWQ — Surface Water Quantity";
      legendItems = [
        { label: "Deep / Permanent (0.8 - 1.0)", color: "#08589e" },
        { label: "Major Reservoirs (0.6 - 0.8)", color: "#2b8cbe" },
        { label: "Moderate Water (0.4 - 0.6)", color: "#4eb3d3" },
        { label: "Shallow / Wetlands (0.3 - 0.4)", color: "#7bccc4" },
        { label: "Flooded / High Moisture (0.2 - 0.3)", color: "#a8ddb5" },
        { label: "Saturated Soil (0.1 - 0.2)", color: "#ccebc5" },
        { label: "Dry Land (0.0 - 0.1)", color: "#e0f3db" },
        { label: "No Surface Water (0.0)", color: "#f7fcf0" },
      ];
    } else if (activeFilter === 'Suitability') {
      title = "LSI — Land Suitability Index";
      legendItems = [
        { label: "Excellent Suitability (0.7 - 0.8)", color: "#056201" },
        { label: "High Suitability (0.6 - 0.7)", color: "#2bbe74" },
        { label: "Good Suitability (0.5 - 0.6)", color: "#4eb374" },
        { label: "Moderate Suitability (0.4 - 0.5)", color: "#74cc74" },
        { label: "Low-Moderate (0.3 - 0.4)", color: "#a5dd74" },
        { label: "Low Suitability (0.2 - 0.3)", color: "#c5eb74" },
        { label: "Very Low Suitability (0.1 - 0.2)", color: "#dbf374" },
        { label: "Unsuitable (0.0 - 0.1)", color: "#f7fc74" },
      ];
    }

    return (
      <div className="map-legend-card" key={activeFilter}>
        <h4 className="map-legend-title">{title}</h4>
        <div className="map-legend-items">
          {legendItems.map((item, i) => (
            <div key={i} className="map-legend-row">
              <span
                className="map-legend-swatch"
                style={{ backgroundColor: item.color }}
              />
              <span className="map-legend-label">{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <div
        ref={mapContainerRef}
        style={{ width: '100%', height: '100%', background: '#ffffff' }}
      />
      <MapLegend activeFilter={activeFilter} />
      <SpatialInspectorCard inspector={inspector} onClose={handleCloseInspector} />
    </div>
  );
}

export default MoroccoMap;
