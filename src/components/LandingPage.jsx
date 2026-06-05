import { useState, useEffect } from 'react';
import './LandingPage.css';

export default function LandingPage({ onLaunch }) {
  const [activeSlide, setActiveSlide] = useState(1);

  // Setup intersection observer to detect active slide as the user scrolls
  useEffect(() => {
    const observerOptions = {
      root: null,
      rootMargin: '-35% 0px -45% 0px', // focused in the middle of the viewport
      threshold: 0.1
    };

    const observerCallback = (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const slideId = parseInt(entry.target.getAttribute('data-slide-id'), 10);
          setActiveSlide(slideId);
        }
      });
    };

    const observer = new IntersectionObserver(observerCallback, observerOptions);
    
    // Find all slides on the right side
    const slideElements = document.querySelectorAll('.showcase-slide');
    slideElements.forEach((el) => observer.observe(el));

    return () => {
      observer.disconnect();
    };
  }, []);

  const scrollToSection = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="landing-page" id="top">
      {/* Navigation Header */}
      <header className="landing-nav">
        <div className="landing-logo" onClick={() => scrollToSection('top')}>
          <div className="landing-logo-icon"></div>
          GeoAI Morocco
        </div>
        <button className="landing-nav-btn" onClick={() => onLaunch()}>
          Launch Platform
        </button>
      </header>

      {/* Hero Section */}
      <section className="landing-hero-container">
        <div className="landing-hero-split">
          <div className="landing-hero-left">
            <div className="landing-badge">
              <span className="landing-badge-dot"></span>
              GEE & Gemini AI Driven Analytics
            </div>
            
            <h1>Wanna know what's best for agriculture in Morocco and invest?</h1>
            
            <p className="landing-hero-subtitle">
              Morocco's premier climate-resilient decision matrix. Leverage high-resolution multi-spectral remote sensing from Google Earth Engine combined with generative Artificial Intelligence to identify secure aquifer reserves, verify local dam index health, and locate optimal arable lands.
            </p>

            <div className="landing-hero-actions">
              <button className="landing-hero-btn primary" onClick={() => onLaunch()}>
                Launch Interactive Platform
                <span className="btn-icon">→</span>
              </button>
              <button className="landing-hero-btn secondary" onClick={() => scrollToSection('showcase')}>
                Explore GEE Indices
              </button>
            </div>
          </div>

          <div className="landing-hero-right">
            <div className="hero-img-frame">
              <img 
                src="/morocco_modern_agriculture.png" 
                alt="Modern Agriculture in Morocco Souss-Massa region" 
                className="hero-img"
              />
              <div className="hero-img-overlay"></div>
            </div>
          </div>
        </div>
        
        {/* Scroll hint */}
        <div className="landing-scroll-hint" onClick={() => scrollToSection('showcase')}>
          <span>Scroll to explore</span>
          <div className="landing-scroll-arrow"></div>
        </div>
      </section>

      {/* Showcase Scroll slides section */}
      <section className="showcase-section" id="showcase">
        <div className="showcase-container">
          <div className="showcase-title-row">
            <h2>Interactive Multi-Spectral Analysis</h2>
            <p>We harness high-resolution Google Earth Engine data to map agricultural viability and investment risks dynamically.</p>
          </div>

          <div className="showcase-split">
            {/* Left side (Sticky visual card) */}
            <div className="showcase-visuals">
              <div className="showcase-window">
                <div className="window-header">
                  <div className="window-dots">
                    <span className="window-dot"></span>
                    <span className="window-dot"></span>
                    <span className="window-dot"></span>
                  </div>
                  <div className="window-title">
                    {activeSlide === 1 && "INDEX.GROUNDWATER_STORAGE"}
                    {activeSlide === 2 && "INDEX.NDWI_SURFACE_WATER"}
                    {activeSlide === 3 && "INDEX.NDVI_LAND_USE"}
                    {activeSlide === 4 && "GEOAI_CHAT_ADVISOR.EXE"}
                  </div>
                </div>

                <div className="showcase-display-wrapper">
                  {/* Slide 1: Groundwater Storage Anomaly Map Sim */}
                  <div className={`showcase-display map-sim-display ${activeSlide === 1 ? 'active' : ''}`}>
                    <div className="mock-map-canvas dgr-map">
                      <div className="mock-map-terrain">
                        <div className="mock-region souss-massa warning-glow">Souss-Massa</div>
                        <div className="mock-region marrakech-safi">Marrakech-Safi</div>
                      </div>
                      
                      <div className="mock-map-popup">
                        <div className="popup-tag warning">AQUIFER RISK</div>
                        <div className="popup-header">Souss-Massa Basin</div>
                        <div className="popup-row">
                          <span>DGR Level:</span>
                          <span className="popup-val risk">-2.1m/yr (Depleting)</span>
                        </div>
                        <div className="popup-row">
                          <span>Groundwater Storage Anomaly:</span>
                          <span className="popup-val">Low Reserves</span>
                        </div>
                      </div>

                      <div className="mock-map-legend">
                        <div className="legend-bar dgr-gradient"></div>
                        <div className="legend-labels">
                          <span>Depleted</span>
                          <span>Stable</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Slide 2: Surface Water (NDWI) Map Sim */}
                  <div className={`showcase-display map-sim-display ${activeSlide === 2 ? 'active' : ''}`}>
                    <div className="mock-map-canvas ndwi-map">
                      <div className="mock-map-terrain">
                        <div className="mock-reservoir al-massira active-glow">Al Massira</div>
                        <div className="mock-river oum-er-rbia">Oum Er-Rbia</div>
                      </div>

                      <div className="mock-map-popup">
                        <div className="popup-tag info">WATER SOURCE</div>
                        <div className="popup-header">Al Massira Dam</div>
                        <div className="popup-row">
                          <span>NDWI Index:</span>
                          <span className="popup-val safe">+0.28 (Water Body)</span>
                        </div>
                        <div className="popup-row">
                          <span>Reservoir capacity:</span>
                          <span className="popup-val">62% (Moderate)</span>
                        </div>
                      </div>

                      <div className="mock-map-legend">
                        <div className="legend-bar ndwi-gradient"></div>
                        <div className="legend-labels">
                          <span>Dry Soil (-1)</span>
                          <span>Water (+1)</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Slide 3: Land Use (NDVI) Map Sim */}
                  <div className={`showcase-display map-sim-display ${activeSlide === 3 ? 'active' : ''}`}>
                    <div className="mock-map-canvas ndvi-map">
                      <div className="mock-map-terrain grid-overlay">
                        <div className="mock-pixel p1 green">0.78</div>
                        <div className="mock-pixel p2 yellow">0.42</div>
                        <div className="mock-pixel p3 green">0.81</div>
                        <div className="mock-pixel p4 green">0.69</div>
                      </div>

                      <div className="mock-map-popup">
                        <div className="popup-tag success">CROP HEALTH</div>
                        <div className="popup-header">Gharb Agricultural Plain</div>
                        <div className="popup-row">
                          <span>NDVI Value:</span>
                          <span className="popup-val success">0.74 (Optimal Yield)</span>
                        </div>
                        <div className="popup-row">
                          <span>Land classification:</span>
                          <span className="popup-val">Irrigated Crops</span>
                        </div>
                      </div>

                      <div className="mock-map-legend">
                        <div className="legend-bar ndvi-gradient"></div>
                        <div className="legend-labels">
                          <span>Barren (0)</span>
                          <span>Dense Canopy (1)</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Slide 4: AI Advisor Chat Sim */}
                  <div className={`showcase-display chat-sim-display ${activeSlide === 4 ? 'active' : ''}`}>
                    <div className="mock-chat-header">
                      <div className="chat-sync-status">
                        <span className="online-indicator"></span>
                        <strong>GEE CHAT DATA SYNCED</strong>
                      </div>
                      <div className="mock-chat-badges">
                        <span className="chat-badge">📅 2024</span>
                        <span className="chat-badge">📊 Land Use (NDVI)</span>
                        <span className="chat-badge">📍 Marrakech-Safi</span>
                      </div>
                    </div>
                    <div className="mock-chat-messages">
                      <div className="mock-chat-bubble user">
                        Is Marrakech-Safi safe for olive orchard investment in 2024?
                      </div>
                      <div className="mock-chat-bubble advisor">
                        <p style={{ margin: '0 0 6px 0', color: '#7BD4E9' }}><strong>🤖 GeoAI Advisor:</strong></p>
                        <p style={{ margin: 0 }}>Marrakech-Safi shows <strong>Moderate Viability</strong> for 2024. NDVI data indicates healthy vegetation density (0.68) in arable valleys, but historical Groundwater Storage Anomaly (GWSA) trends suggest groundwater table drop. Drip-irrigation is highly recommended.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Right side (Scroll trigger text content) */}
            <div className="showcase-content">
              <div className="showcase-slide" data-slide-id="1">
                <span className="slide-number">01 / AQUIFER RESERVES</span>
                <h3>Groundwater Storage Anomaly (GWSA)</h3>
                <p>
                  Assess subterranean water supplies before breaking ground. Track years of GEE depth-related indices to uncover region-wide aquifer depletion and select regions with long-term climate-resilient water security.
                </p>
              </div>

              <div className="showcase-slide" data-slide-id="2">
                <span className="slide-number">02 / RESERVOIR HEALTH</span>
                <h3>Normalized Difference Water Index (NDWI)</h3>
                <p>
                  Evaluate surface water resources, humidity indices, and river proximity. The platform computes NDWI indicators to safeguard your crops against immediate drought risks and ensure proximity to vital irrigation lines.
                </p>
              </div>

              <div className="showcase-slide" data-slide-id="3">
                <span className="slide-number">03 / ARABLE SOIL LAND USE</span>
                <h3>Vegetation Indexes & Crop Health (NDVI)</h3>
                <p>
                  Identify fertile lands and crop cycles dynamically. Visualize Land Use indexes and NDVI crop density values mapped down to local commune levels to see where agricultural production thrives.
                </p>
              </div>

              <div className="showcase-slide" data-slide-id="4">
                <span className="slide-number">04 / INTUITIVE ADVICE</span>
                <h3>Intelligent GeoAI Chat Advisor</h3>
                <p>
                  Translate scientific map metrics into plain language. Our conversational assistant interprets active spatial context (year, index, map boundary) in real-time, instantly formulating risks and opportunities for your capital.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Visual Deep Dives */}
      <section className="detail-section dark" id="precision-sensing">
        <div className="detail-container">
          <div className="detail-split">
            <div className="detail-left-text">
              <span className="detail-pre">SATELLITE TELEMETRY</span>
              <h2>Multi-Spectral Remote Sensing Analysis</h2>
              <p>
                Our platform accesses the Google Earth Engine data catalogs to stream satellite imagery from Landsat and Sentinel constellations in real-time. By computing mathematical combinations of light waves, we reveal indicators hidden to the naked eye.
              </p>
              <ul className="detail-bullet-list">
                <li>
                  <strong>Groundwater Storage Anomaly (GWSA)</strong>: Tracks regional water table anomalies to locate secure aquifers.
                </li>
                <li>
                  <strong>Normalized Difference Water Index (NDWI)</strong>: Measures soil moisture and open reservoir water levels to protect investments against dry periods.
                </li>
                <li>
                  <strong>Normalized Difference Vegetation Index (NDVI)</strong>: Measures chlorophyll absorption to monitor crop growth rates and farm expansion trends.
                </li>
              </ul>
            </div>
            <div className="detail-right-img">
              <div className="detail-image-frame">
                <img 
                  src="/satellite_earth_observation.png" 
                  alt="Satellite Earth observation analytics for Morocco agriculture" 
                  className="detail-img"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="detail-section light" id="investor-viability">
        <div className="detail-container">
          <div className="detail-split reverse">
            <div className="detail-left-text">
              <span className="detail-pre">INVESTMENT STRATEGY</span>
              <h2>Climate-Resilient Agricultural Capital Allocation</h2>
              <p>
                With groundwater aquifers declining in specific zones of Morocco, standard crop placement is no longer viable. Our GeoAI Decision engine guides capital towards optimal crops based on the climate risk profile of each administrative commune.
              </p>
              <div className="detail-metrics-grid">
                <div className="metric-item">
                  <span className="metric-number">92%</span>
                  <span className="metric-label">Water Sync Accuracy</span>
                </div>
                <div className="metric-item">
                  <span className="metric-number">12</span>
                  <span className="metric-label">Regions Analyzed</span>
                </div>
                <div className="metric-item">
                  <span className="metric-number">GEE</span>
                  <span className="metric-label">Earth Engine Backed</span>
                </div>
              </div>
            </div>
            <div className="detail-right-img">
              <div className="detail-image-frame">
                <img 
                  src="/morocco_citrus_farming.png" 
                  alt="Citrus and olive groves under the Atlas mountains in Morocco" 
                  className="detail-img"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature Explanation Grid Section */}
      <section className="landing-explain">
        <div className="explain-header">
          <h2>Platform Insights at a Glance</h2>
          <p>Morocco GeoAI integrates state-of-the-art satellite data streams to deliver actionable agricultural intelligence.</p>
        </div>

        <div className="explain-grid">
          <div className="explain-card">
            <div className="explain-icon-wrapper">🌍</div>
            <h3>Google Earth Engine (GEE)</h3>
            <p>Access real-time multi-spectral satellite imagery. Map vegetation cover, surface soil humidity, and deep hydrology maps updated dynamically.</p>
          </div>

          <div className="explain-card">
            <div className="explain-icon-wrapper">📍</div>
            <h3>Spatial Inspector</h3>
            <p>Click anywhere on the map of Morocco to trigger a point-based GEE inspection. Receive instant coordinate values, water availability, and suitability classifications.</p>
          </div>

          <div className="explain-card">
            <div className="explain-icon-wrapper">🤖</div>
            <h3>Synched Chat Context</h3>
            <p>The AI Chat advisor is context-aware. Toggle "Sync Map Context" so the assistant automatically knows which year, index, and region you are looking at.</p>
          </div>
        </div>
      </section>

      {/* Call to Action Section */}
      <section className="landing-cta-section">
        <div className="landing-cta-box">
          <h2>Ready to discover the best agricultural investments?</h2>
          <p>Launch the interactive platform and start analyzing Morocco's water and soil viability metrics in real-time.</p>
          <button className="landing-cta-btn" onClick={() => onLaunch()}>
            Enter Platform Interface
            <span className="landing-cta-btn-icon">→</span>
          </button>
          <div className="landing-cta-subtext">
            ⚡ POWERED BY GOOGLE EARTH ENGINE & GEMINI PRO
          </div>
        </div>
      </section>
    </div>
  );
}
