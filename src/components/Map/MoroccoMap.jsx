import React, { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

function MoroccoMap() {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);

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

  return (
    <div
      ref={mapContainerRef}
      style={{ width: '100%', height: '100%', background: '#ffffffff' }}
    />
  );
}

export default MoroccoMap;
