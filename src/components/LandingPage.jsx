import { useState, useEffect, useRef } from 'react';
import './LandingPage.css';

/* ── Animated Counter Component ── */
function AnimatedCounter({ end, suffix = '', prefix = '', duration = 2000 }) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const counted = useRef(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !counted.current) {
          counted.current = true;
          const isNum = typeof end === 'number';
          if (!isNum) { setCount(end); return; }
          const startTime = performance.now();
          const animate = (now) => {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
            setCount(Math.round(eased * end));
            if (progress < 1) requestAnimationFrame(animate);
          };
          requestAnimationFrame(animate);
        }
      },
      { threshold: 0.3 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [end, duration]);

  return (
    <span ref={ref} className="metric-number">
      {prefix}{typeof end === 'number' ? count : count}{suffix}
    </span>
  );
}

export default function LandingPage({ onLaunch }) {
  const [activeSlide, setActiveSlide] = useState(1);

  // Setup intersection observer to detect active slide as the user scrolls
  useEffect(() => {
    const observerOptions = {
      root: null,
      rootMargin: '-35% 0px -45% 0px',
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
    const slideElements = document.querySelectorAll('.showcase-slide');
    slideElements.forEach((el) => observer.observe(el));

    return () => { observer.disconnect(); };
  }, []);

  // Scroll-reveal animation for sections
  useEffect(() => {
    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
          }
        });
      },
      { threshold: 0.15, rootMargin: '0px 0px -50px 0px' }
    );

    document.querySelectorAll('.reveal-on-scroll').forEach((el) => {
      revealObserver.observe(el);
    });

    return () => revealObserver.disconnect();
  }, []);

  const scrollToSection = (id) => {
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="landing-page" id="top">
      {/* ── Navigation Header ── */}
      <header className="landing-nav">
        <div className="landing-logo" onClick={() => scrollToSection('top')}>
          <div className="landing-logo-icon"></div>
          Ardi Invest
        </div>
        <nav className="landing-nav-links">
          <button className="nav-link" onClick={() => scrollToSection('showcase')}>Features</button>
          <button className="nav-link" onClick={() => scrollToSection('how-it-works')}>How It Works</button>
          <button className="nav-link" onClick={() => scrollToSection('precision-sensing')}>Technology</button>
        </nav>
        <button className="landing-nav-btn" onClick={() => onLaunch()}>
          Launch Platform →
        </button>
      </header>

      {/* ── Hero Section ── */}
      <section className="landing-hero-container">
        {/* Floating particles */}
        <div className="landing-particles">
          {[...Array(12)].map((_, i) => <div key={i} className="particle"></div>)}
        </div>

        {/* Orbiting rings */}
        <div className="hero-orbit-ring ring-1"></div>
        <div className="hero-orbit-ring ring-2"></div>

        <div className="landing-hero-split">
          <div className="landing-hero-left">
            <div className="landing-badge">
              <span className="landing-badge-dot"></span>
              GEE & Gemini AI Driven Analytics
            </div>
            
            <h1>Smart Agricultural Investment Intelligence for Morocco</h1>
            
            <p className="landing-hero-subtitle">
              Leverage satellite-powered multi-spectral analysis from Google Earth Engine, combined with Gemini AI, to identify secure aquifer reserves, assess land suitability, and make climate-resilient investment decisions across all 12 regions.
            </p>

            <div className="landing-hero-actions">
              <button className="landing-hero-btn primary" onClick={() => onLaunch()}>
                Launch Interactive Platform
                <span className="btn-icon">→</span>
              </button>
              <button className="landing-hero-btn secondary" onClick={() => scrollToSection('showcase')}>
                Explore Features
              </button>
            </div>

            {/* Trust indicators */}
            <div className="hero-trust-row">
              <div className="trust-item">
                <span className="trust-icon">🛰️</span>
                <span>Sentinel-2 & GRACE</span>
              </div>
              <div className="trust-divider"></div>
              <div className="trust-item">
                <span className="trust-icon">🤖</span>
                <span>Gemini Pro AI</span>
              </div>
              <div className="trust-divider"></div>
              <div className="trust-item">
                <span className="trust-icon">📊</span>
                <span>7 GEE Indices</span>
              </div>
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
              {/* Floating stat cards on hero image */}
              <div className="hero-float-card float-top-right">
                <span className="float-card-icon">💧</span>
                <div>
                  <div className="float-card-value">-2.1 cm</div>
                  <div className="float-card-label">GWSA Deficit</div>
                </div>
              </div>
              <div className="hero-float-card float-bottom-left">
                <span className="float-card-icon">🌾</span>
                <div>
                  <div className="float-card-value">0.74</div>
                  <div className="float-card-label">NDVI Index</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Scroll hint */}
        <div className="landing-scroll-hint" onClick={() => scrollToSection('stats-bar')}>
          <span>Scroll to explore</span>
          <div className="landing-scroll-arrow"></div>
        </div>
      </section>

      {/* ── Animated Stats Bar ── */}
      <section className="stats-bar-section" id="stats-bar">
        <div className="stats-bar">
          <div className="stat-item reveal-on-scroll">
            <AnimatedCounter end={7} />
            <span className="stat-label">GEE Spectral Indices</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-item reveal-on-scroll">
            <AnimatedCounter end={12} />
            <span className="stat-label">Regions Analyzed</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-item reveal-on-scroll">
            <AnimatedCounter end={40} suffix="+" />
            <span className="stat-label">Communes Mapped</span>
          </div>
          <div className="stat-divider"></div>
          <div className="stat-item reveal-on-scroll">
            <AnimatedCounter end={2017} prefix="" suffix="–2024" duration={1500} />
            <span className="stat-label">Temporal Coverage</span>
          </div>
        </div>
      </section>

      {/* ── Showcase Scroll Slides Section ── */}
      <section className="showcase-section" id="showcase">
        <div className="showcase-container">
          <div className="showcase-title-row reveal-on-scroll">
            <span className="section-tag">CORE ANALYSIS</span>
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
                  {/* Slide 1: Groundwater */}
                  <div className={`showcase-display map-sim-display ${activeSlide === 1 ? 'active' : ''}`}>
                    <div className="mock-map-canvas dgr-map">
                      <div className="mock-map-terrain">
                        <div className="mock-region souss-massa warning-glow">Souss-Massa</div>
                        <div className="mock-region marrakech-safi">Marrakech-Safi</div>
                      </div>
                      <div className="mock-map-popup">
                        <div className="popup-tag warning">AQUIFER RISK</div>
                        <div className="popup-header">Souss-Massa Basin</div>
                        <div className="popup-row"><span>DGR Level:</span><span className="popup-val risk">-2.1m/yr (Depleting)</span></div>
                        <div className="popup-row"><span>Storage Anomaly:</span><span className="popup-val">Low Reserves</span></div>
                      </div>
                      <div className="mock-map-legend">
                        <div className="legend-bar dgr-gradient"></div>
                        <div className="legend-labels"><span>Depleted</span><span>Stable</span></div>
                      </div>
                    </div>
                  </div>

                  {/* Slide 2: Surface Water */}
                  <div className={`showcase-display map-sim-display ${activeSlide === 2 ? 'active' : ''}`}>
                    <div className="mock-map-canvas ndwi-map">
                      <div className="mock-map-terrain">
                        <div className="mock-reservoir al-massira active-glow">Al Massira</div>
                        <div className="mock-river oum-er-rbia">Oum Er-Rbia</div>
                      </div>
                      <div className="mock-map-popup">
                        <div className="popup-tag info">WATER SOURCE</div>
                        <div className="popup-header">Al Massira Dam</div>
                        <div className="popup-row"><span>NDWI Index:</span><span className="popup-val safe">+0.28 (Water Body)</span></div>
                        <div className="popup-row"><span>Capacity:</span><span className="popup-val">62% (Moderate)</span></div>
                      </div>
                      <div className="mock-map-legend">
                        <div className="legend-bar ndwi-gradient"></div>
                        <div className="legend-labels"><span>Dry Soil (-1)</span><span>Water (+1)</span></div>
                      </div>
                    </div>
                  </div>

                  {/* Slide 3: Land Use */}
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
                        <div className="popup-row"><span>NDVI Value:</span><span className="popup-val success">0.74 (Optimal Yield)</span></div>
                        <div className="popup-row"><span>Classification:</span><span className="popup-val">Irrigated Crops</span></div>
                      </div>
                      <div className="mock-map-legend">
                        <div className="legend-bar ndvi-gradient"></div>
                        <div className="legend-labels"><span>Barren (0)</span><span>Dense Canopy (1)</span></div>
                      </div>
                    </div>
                  </div>

                  {/* Slide 4: AI Advisor */}
                  <div className={`showcase-display chat-sim-display ${activeSlide === 4 ? 'active' : ''}`}>
                    <div className="mock-chat-header">
                      <div className="chat-sync-status">
                        <span className="online-indicator"></span>
                        <strong>GEE CHAT DATA SYNCED</strong>
                      </div>
                      <div className="mock-chat-badges">
                        <span className="chat-badge">📅 2024</span>
                        <span className="chat-badge">🚜 Land Suitability (LSI)</span>
                        <span className="chat-badge">📍 Souss-Massa</span>
                      </div>
                    </div>
                    <div className="mock-chat-messages">
                      <div className="mock-chat-bubble user">
                        Analyze Souss-Massa agricultural suitability and water risk in 2024.
                      </div>
                      <div className="mock-chat-bubble advisor">
                        <p style={{ margin: '0 0 6px 0', color: '#7BD4E9' }}><strong>🤖 Ardi Invest Advisor:</strong></p>
                        <p style={{ margin: 0 }}>Souss-Massa shows <strong>Moderate Viability (46/100)</strong>. Groundwater Recharge (GWR) is extremely low (0.19 cm/yr). We recommend <strong>Majhool Date Palms</strong> or <strong>Argan Trees</strong>, and warn against high-water crops.</p>
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
                <h3>Groundwater Storage & Recharge (GWSA & GWR)</h3>
                <p>Assess subterranean supply and replenishment trends. Track gravity anomalies via GRACE (GWSA) alongside active recharge infiltration rates (GWR) derived from GLDAS land metadata, ensuring long-term climate-resilient water access.</p>
                <div className="slide-tags">
                  <span className="slide-tag">GRACE Satellite</span>
                  <span className="slide-tag">GLDAS</span>
                  <span className="slide-tag">Aquifer Mapping</span>
                </div>
              </div>

              <div className="showcase-slide" data-slide-id="2">
                <span className="slide-number">02 / RESERVOIR & BASIN HEALTH</span>
                <h3>Surface Moisture & Water Quantity (NDWI & SWQ)</h3>
                <p>Evaluate irrigation buffers and reservoir health. The platform combines Sentinel-2 NDWI surface moisture with scaled Surface Water Quantity (SWQ) indices to map open canal, lake, and reservoir abundance.</p>
                <div className="slide-tags">
                  <span className="slide-tag">Sentinel-2</span>
                  <span className="slide-tag">NDWI</span>
                  <span className="slide-tag">Dam Monitoring</span>
                </div>
              </div>

              <div className="showcase-slide" data-slide-id="3">
                <span className="slide-number">03 / ARABLE SOIL & LAND SUITABILITY</span>
                <h3>Vegetation Canopy & Land Suitability Index (NDVI & LSI)</h3>
                <p>Locate fertile zones instantly. Track crop vegetation vigor via Sentinel-2 NDVI canopy density, and compute multi-spectral Land Suitability Index (LSI) scores combining soil wetness and leaf greenness.</p>
                <div className="slide-tags">
                  <span className="slide-tag">NDVI</span>
                  <span className="slide-tag">LSI</span>
                  <span className="slide-tag">Crop Health</span>
                </div>
              </div>

              <div className="showcase-slide" data-slide-id="4">
                <span className="slide-number">04 / CONTEXT-AWARE ADVISOR</span>
                <h3>Synched Chat Advisor & Decisions Engine</h3>
                <p>Get direct agricultural recommendations in plain language. The conversational assistant reads your map's active location and GEE indices to generate tailored soil treatment, crop advice, and investment guidelines.</p>
                <div className="slide-tags">
                  <span className="slide-tag">Gemini Pro</span>
                  <span className="slide-tag">Context Sync</span>
                  <span className="slide-tag">Crop Matching</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── How It Works — Step Flow ── */}
      <section className="how-it-works-section" id="how-it-works">
        <div className="how-container">
          <div className="section-header reveal-on-scroll">
            <span className="section-tag">WORKFLOW</span>
            <h2>How Ardi Invest Works</h2>
            <p>From satellite data to actionable agricultural intelligence — in three simple steps.</p>
          </div>

          <div className="steps-flow">
            <div className="step-card reveal-on-scroll">
              <div className="step-number-circle">1</div>
              <div className="step-icon">🛰️</div>
              <h3>Satellite Data Ingestion</h3>
              <p>Google Earth Engine streams multi-spectral imagery from Sentinel-2, Landsat, and GRACE satellites. Our backend computes 7 environmental indices across Morocco in real-time.</p>
            </div>
            <div className="step-connector">
              <div className="connector-line"></div>
              <div className="connector-dot"></div>
            </div>
            <div className="step-card reveal-on-scroll">
              <div className="step-number-circle">2</div>
              <div className="step-icon">🗺️</div>
              <h3>Interactive Map Exploration</h3>
              <p>Explore choropleth heatmaps of water reserves, vegetation cover, and land suitability. Click any point to trigger a live GEE pixel inspection with 7-layer composite data.</p>
            </div>
            <div className="step-connector">
              <div className="connector-line"></div>
              <div className="connector-dot"></div>
            </div>
            <div className="step-card reveal-on-scroll">
              <div className="step-number-circle">3</div>
              <div className="step-icon">🤖</div>
              <h3>AI-Powered Recommendations</h3>
              <p>The Gemini-powered advisor reads your map's context — year, location, and all 7 indices — to generate tailored crop recommendations, risk assessments, and investment guidance.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Visual Deep Dives ── */}
      <section className="detail-section dark" id="precision-sensing">
        <div className="detail-container">
          <div className="detail-split reveal-on-scroll">
            <div className="detail-left-text">
              <span className="detail-pre">SATELLITE TELEMETRY</span>
              <h2>Multi-Spectral Remote Sensing Analysis</h2>
              <p>Our platform accesses the Google Earth Engine data catalogs to stream satellite imagery from Landsat and Sentinel constellations in real-time. By computing mathematical combinations of light waves, we reveal indicators hidden to the naked eye.</p>
              <ul className="detail-bullet-list">
                <li><strong>Groundwater Storage (GWSA) & Recharge (GWR)</strong>: Tracks deep regional aquifer changes, water table drops, and annual replenishment rates.</li>
                <li><strong>Surface Water (NDWI) & Quantity (SWQ)</strong>: Measures soil moisture levels and scales open water pixels to protect against immediate drought risk.</li>
                <li><strong>Vegetation Canopy (NDVI) & Land Suitability Index (LSI)</strong>: Monitors crop health and computes multi-spectral agricultural suitability scores.</li>
              </ul>
            </div>
            <div className="detail-right-img">
              <div className="detail-image-frame">
                <img src="/satellite_earth_observation.png" alt="Satellite Earth observation analytics for Morocco agriculture" className="detail-img" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="detail-section light" id="investor-viability">
        <div className="detail-container">
          <div className="detail-split reverse reveal-on-scroll">
            <div className="detail-left-text">
              <span className="detail-pre">INVESTMENT STRATEGY</span>
              <h2>Climate-Resilient Agricultural Capital Allocation</h2>
              <p>With groundwater aquifers declining in specific zones of Morocco, standard crop placement is no longer viable. Our GeoAI Decision engine guides capital towards optimal crops based on the climate risk profile of each administrative commune.</p>
              <div className="detail-metrics-grid">
                <div className="metric-item">
                  <AnimatedCounter end={92} suffix="%" />
                  <span className="metric-label">Water Sync Accuracy</span>
                </div>
                <div className="metric-item">
                  <AnimatedCounter end={12} />
                  <span className="metric-label">Regions Analyzed</span>
                </div>
                <div className="metric-item">
                  <AnimatedCounter end={0} prefix="" suffix="GEE" duration={0} />
                  <span className="metric-label">Earth Engine Backed</span>
                </div>
              </div>
            </div>
            <div className="detail-right-img">
              <div className="detail-image-frame">
                <img src="/morocco_citrus_farming.png" alt="Citrus and olive groves under the Atlas mountains in Morocco" className="detail-img" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 7-Layer Index Grid ── */}
      <section className="index-grid-section">
        <div className="index-grid-container">
          <div className="section-header reveal-on-scroll">
            <span className="section-tag">7-LAYER ANALYSIS</span>
            <h2>Complete Environmental Index Suite</h2>
            <p>Every location in Morocco is evaluated across seven complementary spectral and hydrological indices.</p>
          </div>

          <div className="index-cards-grid">
            {[
              { icon: '💧', name: 'GWSA', full: 'Groundwater Storage Anomaly', desc: 'GRACE satellite gravity anomalies tracking deep aquifer volume changes over time.', color: '#4575b4' },
              { icon: '🕳️', name: 'GWD', full: 'Groundwater Depth Change', desc: 'Water table depth fluctuations computed from GLDAS hydrological model outputs.', color: '#91bfdb' },
              { icon: '🌧️', name: 'GWR', full: 'Groundwater Recharge', desc: 'Annual infiltration rate estimating how fast precipitation replenishes aquifers.', color: '#2171b5' },
              { icon: '🌊', name: 'NDWI', full: 'Surface Water Index', desc: 'Sentinel-2 normalized difference water index mapping surface moisture levels.', color: '#1E90FF' },
              { icon: '💧', name: 'SWQ', full: 'Surface Water Quantity', desc: 'Scaled open water pixel density measuring reservoir and canal abundance.', color: '#4eb3d3' },
              { icon: '🌾', name: 'NDVI', full: 'Vegetation Cover', desc: 'Sentinel-2 normalized difference vegetation index monitoring crop canopy density.', color: '#10b981' },
              { icon: '🚜', name: 'LSI', full: 'Land Suitability Index', desc: 'Multi-spectral composite score combining soil wetness and leaf greenness.', color: '#056201' },
            ].map((idx, i) => (
              <div key={i} className="index-card reveal-on-scroll" style={{ '--index-color': idx.color }}>
                <div className="index-card-header">
                  <span className="index-card-icon">{idx.icon}</span>
                  <span className="index-card-code">{idx.name}</span>
                </div>
                <h4>{idx.full}</h4>
                <p>{idx.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Feature Explanation Grid Section ── */}
      <section className="landing-explain">
        <div className="explain-header reveal-on-scroll">
          <span className="section-tag">PLATFORM FEATURES</span>
          <h2>Platform Insights at a Glance</h2>
          <p>Ardi Invest integrates state-of-the-art satellite data streams to deliver actionable agricultural intelligence.</p>
        </div>

        <div className="explain-grid">
          <div className="explain-card reveal-on-scroll">
            <div className="explain-icon-wrapper">🌍</div>
            <h3>Google Earth Engine (GEE)</h3>
            <p>Access real-time multi-spectral satellite imagery. Map vegetation cover, surface soil humidity, and deep hydrology maps updated dynamically.</p>
          </div>
          <div className="explain-card reveal-on-scroll">
            <div className="explain-icon-wrapper">📍</div>
            <h3>Spatial Inspector</h3>
            <p>Click anywhere on the map of Morocco to trigger a point-based GEE inspection. Receive instant coordinate values, water availability, and suitability classifications.</p>
          </div>
          <div className="explain-card reveal-on-scroll">
            <div className="explain-icon-wrapper">🤖</div>
            <h3>Synched Chat Context</h3>
            <p>The AI Chat advisor is context-aware. Toggle "Sync Map Context" so the assistant automatically knows which year, index, and region you are looking at.</p>
          </div>
          <div className="explain-card reveal-on-scroll">
            <div className="explain-icon-wrapper">🚜</div>
            <h3>7-Layer Decision Matrix</h3>
            <p>Query GWSA, GWD, Recharge, NDWI, SWQ, NDVI, and LSI in parallel. Instantly receive crop matching rules and climate-resilient farming advice.</p>
          </div>
        </div>
      </section>

      {/* ── Call to Action Section ── */}
      <section className="landing-cta-section">
        <div className="landing-cta-box reveal-on-scroll">
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

      {/* ── Footer ── */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <div className="footer-brand-dot"></div>
            Ardi Invest
          </div>
          <div className="footer-meta">
            <div className="footer-tech">
              <span>React</span>
              <span>FastAPI</span>
              <span>Google Earth Engine</span>
              <span>Gemini Pro AI</span>
              <span>Leaflet.js</span>
            </div>
            <div className="footer-copy">© 2024 Ardi Invest — Climate-Resilient Agricultural Investment Intelligence for Morocco</div>
          </div>
        </div>
      </footer>
    </div>
  );
}
