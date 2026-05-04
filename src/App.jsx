import { useState } from 'react';
import MoroccoMap from './components/Map/MoroccoMap.jsx';
import './App.css';

function App() {
  const [activeFilter, setActiveFilter] = useState('Groundwater');
  const [selectedYear, setSelectedYear] = useState(2003);
  const [adminLevel, setAdminLevel] = useState('admin0-all');
  return (
    <div className="platform">
      <header className="topbar">
        <span>PLATEFORM GeoAi</span>
      </header>
      <main className="layout">
        <aside className="sidebar">COMMENTAIRE</aside>
        <section className="map-area">
          <div className="toolbar">
            <button
              onClick={() => setActiveFilter('Groundwater')}
              className={activeFilter === 'Groundwater' ? 'active' : ''}>
                Groundwater
            </button>
            <button
              onClick={() => setActiveFilter('Surface Water')}
              className={activeFilter === 'Surface Water' ? 'active' : ''}>
                Surface Water
            </button>
            <button
              onClick={() => setActiveFilter('Land Use')}
              className={activeFilter === 'Land Use' ? 'active' : ''}>
            Land Use
            </button>
            <button
              onClick={() => setActiveFilter('Decision Making')}
              className={activeFilter === 'Decision Making' ? 'active' : ''}>
            Decision Making
            </button>
          </div>
          <div className="map-canvas">
            <MoroccoMap selectedYear={selectedYear} activeFilter={activeFilter} />
            </div>
        </section>
        <aside className="info-panel">
          <div>
            <label>YEAR</label>
            <input type="range" min="2003" max="2024" step="1" defaultValue="2003" onChange={(e) => setSelectedYear(e.target.value)} />
            <span>{selectedYear}</span>
          </div>
            <div className="admin-buttons">
              <button
              onClick={() => setAdminLevel('admin0-all')}
              className={adminLevel === 'admin0-all' ? 'admin-btn active' : 'admin-btn'}>
              Admin0 : All the map
              </button>
              <button
              onClick={() => setAdminLevel('admin1-communes')}
              className={adminLevel === 'admin1-communes' ? 'admin-btn active' : 'admin-btn'}>
              Admin1 : Communes
              </button>
              <button
              onClick={() => setAdminLevel('admin2-regions')}
              className={adminLevel === 'admin2-regions' ? 'admin-btn active' : 'admin-btn'}>
              Admin2 : Regions
            </button>
          </div>
        </aside>
      </main>
    </div>
  );
}

export default App;
