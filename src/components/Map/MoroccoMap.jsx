import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getAdmin2TileUrl } from '../../services/apii';
import { getTileUrl } from '../../services/apii';

function MoroccoMap({ selectedYear, activeFilter, adminLevel }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const regionsLayerRef = useRef(null);
  const satelliteLayerRef = useRef(null);
 
  useEffect(() => {
    if (!mapContainerRef.current) return;

    // 1. Initialize the Leaflet map centered directly over Morocco
    const map = L.map(mapContainerRef.current, {
      center: [31.5, -7.5],
      zoom: 5.3,
      zoomControl: true,
      attributionControl: false // Cleans up the footer attribution list
    });

    // 2. Add an elegant light-mode basemap layer (CartoDB Positron)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19
    }).addTo(map);

    // Save the instance reference
    mapInstanceRef.current = map;

    // 3. Clean up the map container when the component is unmounted
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Handle dynamic loading of Admin2 Regions tile layer
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    

    if (adminLevel === 'admin2-regions') {
      // Fetch GEE tile URL for Morocco regions
      getAdmin2TileUrl()
        .then((tileUrl) => {
          if (!mapInstanceRef.current) return; // Ensure map is still mounted

          // Remove existing regions layer if present
          if (regionsLayerRef.current) {
            mapInstanceRef.current.removeLayer(regionsLayerRef.current);
          }

          // Add the GEE border tile layer
          const newLayer = L.tileLayer(tileUrl, {
            maxZoom: 19
          }).addTo(mapInstanceRef.current);

          regionsLayerRef.current = newLayer;
        })
        .catch((err) => {
          console.error("Error loading admin2 regions tile layer:", err);
        });
    } else {
      // Remove layer if adminLevel is not 'admin2-regions'
      if (regionsLayerRef.current) {
        map.removeLayer(regionsLayerRef.current);
        regionsLayerRef.current = null;
      }
    }
  }, [adminLevel]);

  // Handle dynamic loading of satellite index overlay layer (Groundwater, Surface Water, Land Use)
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (activeFilter && activeFilter !== 'Decision Making') {
      // 1. Fetch GEE tile URL (getTileUrl is async and returns a Promise)
      getTileUrl(activeFilter, selectedYear)
        .then((tileUrl) => {
          if (!mapInstanceRef.current) return; // Ensure map is still mounted

          // 2. Remove the previous satellite layer to prevent stacking
          if (satelliteLayerRef.current) {
            mapInstanceRef.current.removeLayer(satelliteLayerRef.current);
          }

          // 3. Create and add the new satellite tile layer (with nice semi-transparency)
          const newLayer = L.tileLayer(tileUrl, {
            maxZoom: 19,
            opacity: 1
          }).addTo(mapInstanceRef.current);

          satelliteLayerRef.current = newLayer;
        })
        .catch((err) => {
          console.error("Error loading GEE satellite tile layer:", err);
        });
    } else {
      // Clear satellite layer if no filter is selected or if it's 'Decision Making'
      if (satelliteLayerRef.current) {
        map.removeLayer(satelliteLayerRef.current);
        satelliteLayerRef.current = null;
      }
    }
  }, [activeFilter, selectedYear]);


// Helper component to render a premium floating card legend
function MapLegend({ activeFilter }) {
  if (!activeFilter || activeFilter === 'Decision Making') return null;

  const cardStyle = {
    position: 'absolute',
    bottom: '24px',
    right: '24px',
    zIndex: 1000,
    background: 'rgba(255, 255, 255, 0.95)',
    padding: '16px',
    borderRadius: '12px',
    boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
    minWidth: '220px',
    border: '1px solid rgba(226, 232, 240, 0.8)',
    fontFamily: "system-ui, -apple-system, sans-serif"
  };

  const titleStyle = {
    margin: '0 0 10px',
    fontSize: '13px',
    fontWeight: '700',
    color: '#0F172A',
    textTransform: 'uppercase',
    letterSpacing: '0.5px',
    borderBottom: '1px solid #E2E8F0',
    paddingBottom: '6px'
  };

  if (activeFilter === 'Groundwater') {
    return (
      <div style={cardStyle}>
        <h4 style={titleStyle}>Indice de Nappe (GW)</h4>
        <div style={{ fontSize: '12px', color: '#475569', marginBottom: '8px' }}>
          Anomalie de l'eau (CSR)
        </div>
        <div style={{
          background: 'linear-gradient(to right, white, cyan, blue)',
          height: '14px',
          borderRadius: '4px',
          margin: '8px 0 6px',
          border: '1px solid rgba(0,0,0,0.1)'
        }} />
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#64748B', fontWeight: 'bold' }}>
          <span>Sec (-1.5 cm)</span>
          <span>Humide (+1.5 cm)</span>
        </div>
      </div>
    );
  }

  const legendItems = activeFilter === 'Surface Water' ? [
    { label: "Eau Permanente (0.5)", color: "#0000CD" },
    { label: "Plans d'eau (0.3)", color: "#1E90FF" },
    { label: "Eau peu profonde (0.1)", color: "#87CEEB" },
    { label: "Sol Humide (0.0)", color: "#FFFACD" },
    { label: "Terre Sèche (-0.2)", color: "#D2691E" },
    { label: "Zone Très Sèche (-0.5)", color: "#8B4513" },
  ] : [
    { label: "Forêt Dense (0.7+)", color: "#056201" },
    { label: "Végétation Moyenne (0.5)", color: "#74A901" },
    { label: "Végétation Éparse (0.3)", color: "#FCD163" },
    { label: "Agriculture (0.2)", color: "#99B718" },
    { label: "Sol Nu (0.1)", color: "#CE7E45" },
    { label: "Pas de Végétation (0.0)", color: "#FFFFFF" },
  ];

  return (
    <div style={cardStyle}>
      <h4 style={titleStyle}>
        {activeFilter === 'Surface Water' ? 'Indice NDWI - Eau' : 'Indice NDVI - Végétation'}
      </h4>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {legendItems.map((item, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '11.5px', color: '#334155' }}>
            <span style={{
              display: 'inline-block',
              width: '16px',
              height: '16px',
              borderRadius: '4px',
              backgroundColor: item.color,
              border: '1px solid rgba(0,0,0,0.15)',
              flexShrink: 0
            }} />
            <span style={{ fontWeight: '500' }}>{item.label}</span>
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
    </div>
  );
}


export default MoroccoMap;
