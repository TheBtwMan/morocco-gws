import { useState, useEffect, useRef, useCallback } from 'react';
import MoroccoMap from './components/Map/MoroccoMap.jsx';
import { postChatQuery, preloadAllPlatformData } from './services/apii.js';
import LandingPage from './components/LandingPage.jsx';
import RoleSelection from './components/RoleSelection.jsx';
import AdminDashboard from './components/AdminDashboard.jsx';
import './App.css';

const WELCOME_MSG = `### 👋 Welcome to the GeoAI Resource & Investment Advisor!

I am your intelligent assistant linked directly to **Google Earth Engine (GEE)**. I analyze soil, surface moisture, and deep aquifers in Morocco to help you make climate-resilient investment decisions.

#### 💡 How to Interact with Me:
1.  **Ask about a specific region**: Type something like *"Can I invest in Souss-Massa?"* or *"Analyze Marrakech-Safi"*.
2.  **Learn about scientific indices**: Ask *"What is NDWI?"*, *"Explain NDVI"*, or *"How is groundwater measured?"*.
3.  **Use Active Map Context**: Check **"Sync Map Context"** below. When enabled, asking *"Is it safe to invest here?"* will automatically analyze the active region, year, and index currently selected on your map view!

*Select a preset question pill below or type your custom query to begin!*`;

function GeoAIChat({ currentYear, currentIndex, selectedLocation, initialQuery, clearInitialQuery }) {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: WELCOME_MSG, time: new Date() }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [syncMapContext, setSyncMapContext] = useState(true);
  const [streamingText, setStreamingText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState(null);
  
  const chatMessagesRef = useRef(null);
  const streamingRef = useRef(null);

  // Auto-scroll to bottom of chat without shifting the page viewport
  useEffect(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  }, [messages, isLoading, streamingText]);

  // Handle queries passed from the landing page
  useEffect(() => {
    if (initialQuery) {
      const timer = setTimeout(() => {
        handleSend(initialQuery);
        clearInitialQuery();
      }, 100);
      return () => clearTimeout(timer);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialQuery]);

  const presetPrompts = [
    { label: "🌾 Invest in Souss-Massa?", text: "Can I invest in Souss-Massa agricultural projects?" },
    { label: "💧 Best Groundwater region?", text: "Which region in Morocco currently has the best groundwater reserves?" },
    { label: "📈 Marrakech-Safi crop risk?", text: "What are the agricultural and drought investment risks in Marrakech-Safi?" },
    { label: "☀️ Invest in Dakhla solar?", text: "Is Dakhla-Oued Ed-Dahab a good region for renewable energy or solar investments?" },
    { label: "🌊 Explain NDWI water index", text: "Explain the NDWI surface water index and what it tells us." },
    { label: "🕳️ Explain GWD depth", text: "Explain the Groundwater Depth (GWD) index and what it tells us." }
  ];

  // Typewriter streaming effect
  const streamResponse = useCallback((fullText) => {
    setIsStreaming(true);
    setStreamingText('');
    let i = 0;
    const speed = 4; // ms per character
    
    const tick = () => {
      if (i < fullText.length) {
        // Emit larger chunks for speed
        const chunk = fullText.substring(0, i + 3);
        setStreamingText(chunk);
        i += 3;
        streamingRef.current = requestAnimationFrame(() => setTimeout(tick, speed));
      } else {
        setStreamingText('');
        setIsStreaming(false);
        setMessages(prev => [...prev, { role: 'assistant', content: fullText, time: new Date() }]);
      }
    };
    tick();
  }, []);

  // Cleanup streaming on unmount
  useEffect(() => {
    return () => {
      if (streamingRef.current) cancelAnimationFrame(streamingRef.current);
    };
  }, []);

  const handleSend = async (text) => {
    if (!text || text.trim() === '' || isStreaming) return;
    
    const userMsg = { role: 'user', content: text, time: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    try {
      const context = syncMapContext ? {
        year: currentYear,
        index: currentIndex,
        location: selectedLocation
      } : {};
      
      const history = messages.slice(-10);
      const response = await postChatQuery(text, history, context);
      
      setIsLoading(false);
      streamResponse(response);
    } catch (err) {
      console.error(err);
      setIsLoading(false);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `⚠️ **Connection Error**: Failed to reach the GeoAI service. Please make sure the FastAPI server is running at http://localhost:8000.`,
        time: new Date()
      }]);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSend(inputValue);
    }
  };

  const handleClear = () => {
    if (streamingRef.current) cancelAnimationFrame(streamingRef.current);
    setStreamingText('');
    setIsStreaming(false);
    setIsLoading(false);
    setMessages([{ role: 'assistant', content: WELCOME_MSG, time: new Date() }]);
  };

  const handleCopy = (text, idx) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedIdx(idx);
      setTimeout(() => setCopiedIdx(null), 1500);
    });
  };

  const formatTime = (date) => {
    if (!date) return '';
    const d = new Date(date);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // ── Markdown Rendering ──────────────────────────────────────────────────

  function parseInlineMarkdown(text) {
    if (!text) return "";
    // Split on: **bold**, *italic*, `code`
    const parts = text.split(/(\*\*.*?\*\*|`[^`]+`|\*[^*]+\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        const rawText = part.substring(2, part.length - 2);
        if (rawText.includes("HIGH RISK") || rawText.includes("Severe") || rawText.includes("SEVERE")) {
          return <span key={i} className="risk-badge badge-red">{rawText}</span>;
        } else if (rawText.includes("MODERATE RISK") || rawText.includes("Moderate") || rawText.includes("MODERATE")) {
          return <span key={i} className="risk-badge badge-yellow">{rawText}</span>;
        } else if (rawText.includes("HIGH VIABILITY") || rawText.includes("Stable") || rawText.includes("Excellent") || rawText.includes("STRONG")) {
          return <span key={i} className="risk-badge badge-green">{rawText}</span>;
        }
        return <strong key={i} className="md-bold">{rawText}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return <code key={i} className="md-inline-code">{part.substring(1, part.length - 1)}</code>;
      }
      if (part.startsWith('*') && part.endsWith('*') && !part.startsWith('**')) {
        return <em key={i} className="md-italic">{part.substring(1, part.length - 1)}</em>;
      }
      return part;
    });
  }

  function renderMath(line, idx) {
    let formula = line.replace(/^\$\$/, '').replace(/\$\$$/, '').trim();
    formula = formula.replace(/\\text\{([^{}]+)\}/g, '$1');
    formula = formula.replace(/\\times/g, ' × ');
    formula = formula.replace(/\\max/g, 'max');

    const fracMatch = formula.match(/\\frac\{([^{}]+)\}\{([^{}]+)\}/);
    if (fracMatch) {
      const fullMatch = fracMatch[0];
      const numerator = fracMatch[1];
      const denominator = fracMatch[2];
      const parts = formula.split(fullMatch);
      const leftText = parts[0] || "";
      const rightText = parts[1] || "";
      
      return (
        <div key={idx} className="math-block">
          {leftText && <span className="math-text">{leftText}</span>}
          <div className="math-fraction">
            <span className="math-numerator">{numerator}</span>
            <span className="math-denominator">{denominator}</span>
          </div>
          {rightText && <span className="math-text">{rightText}</span>}
        </div>
      );
    }
    return (
      <div key={idx} className="math-block">
        <span className="math-text">{formula}</span>
      </div>
    );
  }

  function renderMarkdown(text) {
    if (!text) return null;
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      const trimmed = line.trim();
      if (!trimmed) return <div key={idx} style={{ height: '6px' }} />;
      if (trimmed === '---') return <hr key={idx} className="md-hr" />;
      
      if (trimmed.startsWith('$$') && trimmed.endsWith('$$')) {
        return renderMath(trimmed, idx);
      }

      if (trimmed.startsWith('### ')) {
        return <h3 key={idx}>{parseInlineMarkdown(trimmed.substring(4))}</h3>;
      }
      if (trimmed.startsWith('#### ')) {
        return <h4 key={idx}>{parseInlineMarkdown(trimmed.substring(5))}</h4>;
      }
      
      if (trimmed.startsWith('>')) {
        let quoteText = trimmed.substring(1).trim();
        let alertClass = 'md-blockquote';
        if (quoteText.startsWith('[!WARNING]')) {
          quoteText = quoteText.replace('[!WARNING]', '').trim();
          alertClass = 'md-alert md-alert-warning';
        } else if (quoteText.startsWith('[!IMPORTANT]')) {
          quoteText = quoteText.replace('[!IMPORTANT]', '').trim();
          alertClass = 'md-alert md-alert-important';
        } else if (quoteText.startsWith('[!TIP]')) {
          quoteText = quoteText.replace('[!TIP]', '').trim();
          alertClass = 'md-alert md-alert-tip';
        }
        return (
          <blockquote key={idx} className={alertClass}>
            {parseInlineMarkdown(quoteText)}
          </blockquote>
        );
      }

      // Numbered lists: "1. ", "2. ", etc.
      const numberedMatch = trimmed.match(/^(\d+)\.\s+(.+)/);
      if (numberedMatch) {
        return (
          <div key={idx} className="md-numbered-item">
            <span className="md-number">{numberedMatch[1]}.</span>
            <span>{parseInlineMarkdown(numberedMatch[2])}</span>
          </div>
        );
      }
      
      // Nested indented list items (4+ spaces followed by * or -)
      if (line.match(/^\s{4,}\*\s/) || line.match(/^\s{4,}-\s/)) {
        const content = trimmed.substring(2);
        return (
          <ul key={idx} className="md-nested-list">
            <li>{parseInlineMarkdown(content)}</li>
          </ul>
        );
      }

      if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
        return (
          <ul key={idx} className="md-list">
            <li>{parseInlineMarkdown(trimmed.substring(2))}</li>
          </ul>
        );
      }
      
      return <p key={idx} className="md-paragraph">{parseInlineMarkdown(trimmed)}</p>;
    });
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-indicator"></div>
        <h3>GeoAI Advisor</h3>
        <button className="chat-clear-btn" onClick={handleClear} title="Clear conversation">
          🗑️
        </button>
      </div>

      <div className="chat-context-box">
        <div className="chat-sync-row">
          <label className="chat-sync-toggle">
            <input 
              type="checkbox" 
              checked={syncMapContext} 
              onChange={(e) => setSyncMapContext(e.target.checked)} 
            />
            Sync Map Context
          </label>
        </div>
        {syncMapContext && (
          <div className="chat-context-badges">
            <span className="context-badge">📅 {currentYear}</span>
            <span className="context-badge">📊 {currentIndex}</span>
          </div>
        )}
      </div>

      <div className="chat-messages" ref={chatMessagesRef}>
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message ${msg.role}`}>
            {msg.role === 'assistant' ? (
              <>
                {renderMarkdown(msg.content)}
                <div className="msg-footer">
                  <span className="msg-timestamp">{formatTime(msg.time)}</span>
                  <button 
                    className={`msg-copy-btn ${copiedIdx === i ? 'copied' : ''}`}
                    onClick={() => handleCopy(msg.content, i)}
                    title="Copy to clipboard"
                  >
                    {copiedIdx === i ? '✓' : '📋'}
                  </button>
                </div>
              </>
            ) : (
              <>
                {msg.content}
                <div className="msg-footer msg-footer-user">
                  <span className="msg-timestamp">{formatTime(msg.time)}</span>
                </div>
              </>
            )}
          </div>
        ))}
        {isStreaming && (
          <div className="chat-message assistant streaming">
            {renderMarkdown(streamingText)}
            <span className="streaming-cursor" />
          </div>
        )}
        {isLoading && (
          <div className="chat-loading">
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
          </div>
        )}
      </div>

      {selectedLocation && syncMapContext && (
        <div className={`chat-synced-location ${selectedLocation.loading ? 'loading' : ''}`}>
          <div className="synced-location-header">
            <span className="location-pin">
              {selectedLocation.title.includes("Region") ? "🗺️" : selectedLocation.title.includes("Commune") ? "🏡" : "📍"}
            </span>
            <div className="location-info">
              <span className="location-title">{selectedLocation.title}</span>
              <span className="location-coords">
                Lat: {parseFloat(selectedLocation.lat).toFixed(4)}, Lon: {parseFloat(selectedLocation.lon).toFixed(4)}
              </span>
            </div>
            <button 
              className="location-analyze-btn" 
              onClick={() => handleSend("Analyze agricultural suitability and water risk for the selected location.")}
              disabled={isLoading || isStreaming || selectedLocation.loading}
            >
              Analyze
            </button>
          </div>
          
          {selectedLocation.loading ? (
            <div className="synced-location-loading">
              <div className="synced-location-spinner"></div>
              <span>Syncing GEE data...</span>
            </div>
          ) : selectedLocation.data && (
            <div className="synced-location-metrics">
              <div className="metric-badge">
                <span className="badge-dot" style={{ backgroundColor: selectedLocation.data.gwsa === null ? '#94a3b8' : selectedLocation.data.gwsa < -0.8 ? '#f87171' : selectedLocation.data.gwsa < 0 ? '#fbbf24' : '#34d399' }} />
                <span>GWSA: {selectedLocation.data.gwsa !== null ? `${selectedLocation.data.gwsa.toFixed(2)} cm` : 'N/A'}</span>
              </div>
              <div className="metric-badge">
                <span className="badge-dot" style={{ backgroundColor: selectedLocation.data.gwd === null ? '#94a3b8' : selectedLocation.data.gwd < -0.4 ? '#f87171' : selectedLocation.data.gwd < 0 ? '#fbbf24' : '#34d399' }} />
                <span>GWD: {selectedLocation.data.gwd !== null ? `${selectedLocation.data.gwd.toFixed(2)} m` : 'N/A'}</span>
              </div>
              <div className="metric-badge">
                <span className="badge-dot" style={{ backgroundColor: selectedLocation.data.recharge === null ? '#94a3b8' : selectedLocation.data.recharge < 0.0 ? '#f87171' : selectedLocation.data.recharge < 4.0 ? '#fbbf24' : '#34d399' }} />
                <span>GWR: {selectedLocation.data.recharge !== null ? `${selectedLocation.data.recharge.toFixed(2)} mm` : 'N/A'}</span>
              </div>
              <div className="metric-badge">
                <span className="badge-dot" style={{ backgroundColor: selectedLocation.data.ndwi === null ? '#94a3b8' : selectedLocation.data.ndwi < -0.2 ? '#f87171' : selectedLocation.data.ndwi < 0.15 ? '#fbbf24' : '#34d399' }} />
                <span>NDWI: {selectedLocation.data.ndwi !== null ? selectedLocation.data.ndwi.toFixed(2) : 'N/A'}</span>
              </div>
              <div className="metric-badge">
                <span className="badge-dot" style={{ backgroundColor: selectedLocation.data.water_quantity === null ? '#94a3b8' : selectedLocation.data.water_quantity < 0.15 ? '#f87171' : selectedLocation.data.water_quantity < 0.4 ? '#fbbf24' : '#34d399' }} />
                <span>SWQ: {selectedLocation.data.water_quantity !== null ? selectedLocation.data.water_quantity.toFixed(2) : 'N/A'}</span>
              </div>
              <div className="metric-badge">
                <span className="badge-dot" style={{ backgroundColor: selectedLocation.data.ndvi === null ? '#94a3b8' : selectedLocation.data.ndvi < 0.15 ? '#f87171' : selectedLocation.data.ndvi < 0.4 ? '#fbbf24' : '#34d399' }} />
                <span>NDVI: {selectedLocation.data.ndvi !== null ? selectedLocation.data.ndvi.toFixed(2) : 'N/A'}</span>
              </div>
              <div className="metric-badge">
                <span className="badge-dot" style={{ backgroundColor: selectedLocation.data.suitability === null ? '#94a3b8' : selectedLocation.data.suitability < 0.35 ? '#f87171' : selectedLocation.data.suitability < 0.6 ? '#fbbf24' : '#34d399' }} />
                <span>LSI: {selectedLocation.data.suitability !== null ? selectedLocation.data.suitability.toFixed(2) : 'N/A'}</span>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="chat-presets">
        <span className="chat-presets-title">Quick Inquiries</span>
        <div className="preset-pills">
          {presetPrompts.map((p, i) => (
            <button 
              key={i} 
              className="preset-pill" 
              onClick={() => handleSend(p.text)}
              disabled={isLoading || isStreaming}
              title={p.text}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="chat-input-bar">
        <input 
          type="text" 
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about indices or investment..."
          disabled={isLoading || isStreaming}
        />
        <button 
          className="chat-send-btn" 
          onClick={() => handleSend(inputValue)}
          disabled={isLoading || isStreaming || !inputValue.trim()}
        >
          Ask
        </button>
      </div>
    </div>
  );
}

function App() {
  const [view, setView] = useState('landing');
  const [initialQuery, setInitialQuery] = useState(null);
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [showAdminPanel, setShowAdminPanel] = useState(false);

  const [activeFilter, setActiveFilter] = useState('GWSA');
  const [gwDropdownOpen, setGwDropdownOpen] = useState(false);
  const [swDropdownOpen, setSwDropdownOpen] = useState(false);
  const [landDropdownOpen, setLandDropdownOpen] = useState(false);

  const gwTimeoutRef = useRef(null);
  const swTimeoutRef = useRef(null);
  const landTimeoutRef = useRef(null);

  const handleMouseEnterGw = () => {
    if (gwTimeoutRef.current) clearTimeout(gwTimeoutRef.current);
    setGwDropdownOpen(true);
  };
  const handleMouseLeaveGw = () => {
    gwTimeoutRef.current = setTimeout(() => setGwDropdownOpen(false), 250);
  };

  const handleMouseEnterSw = () => {
    if (swTimeoutRef.current) clearTimeout(swTimeoutRef.current);
    setSwDropdownOpen(true);
  };
  const handleMouseLeaveSw = () => {
    swTimeoutRef.current = setTimeout(() => setSwDropdownOpen(false), 250);
  };

  const handleMouseEnterLand = () => {
    if (landTimeoutRef.current) clearTimeout(landTimeoutRef.current);
    setLandDropdownOpen(true);
  };
  const handleMouseLeaveLand = () => {
    landTimeoutRef.current = setTimeout(() => setLandDropdownOpen(false), 250);
  };

  useEffect(() => {
    return () => {
      if (gwTimeoutRef.current) clearTimeout(gwTimeoutRef.current);
      if (swTimeoutRef.current) clearTimeout(swTimeoutRef.current);
      if (landTimeoutRef.current) clearTimeout(landTimeoutRef.current);
    };
  }, []);

  const [selectedYear, setSelectedYear] = useState(2017);
  const [debouncedYear, setDebouncedYear] = useState(2017);
  const [adminLevel, setAdminLevel] = useState('admin0-all');
  
  const minYear = 2017;
  const maxYear = 2024;

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedYear(selectedYear);
    }, 300);

    return () => {
      clearTimeout(handler);
    };
  }, [selectedYear]);

  // Dynamically manage body overflow class depending on view routing
  useEffect(() => {
    if (view === 'platform') {
      document.body.classList.add('platform-active');
    } else {
      document.body.classList.remove('platform-active');
    }
    return () => {
      document.body.classList.remove('platform-active');
    };
  }, [view]);

  // Pre-download all platform GEE index layers and average metrics in the background
  useEffect(() => {
    preloadAllPlatformData((progress) => {
      console.log(`📦 Morocco GEE preloader: ${progress}% cached`);
    });
  }, []);

  const handleFilterChange = (filter) => {
    setActiveFilter(filter);
  };

  const handleLaunchPlatform = (query) => {
    if (query) {
      setInitialQuery(query);
    }
    setView('role-select');
  };

  const handleSelectUser = () => {
    setIsAdmin(false);
    setView('platform');
  };

  const handleSelectAdmin = () => {
    setIsAdmin(true);
    setView('platform');
  };

  if (view === 'landing') {
    return <LandingPage onLaunch={handleLaunchPlatform} />;
  }

  if (view === 'role-select') {
    return (
      <RoleSelection
        onSelectUser={handleSelectUser}
        onSelectAdmin={handleSelectAdmin}
        onBack={() => setView('landing')}
      />
    );
  }

  return (
    <div className="platform">
      <header className="topbar">
        <button className="back-hub-btn" onClick={() => setView('role-select')}>
          <span className="back-arrow">←</span> Role Selection
        </button>
        <div className="topbar-brand">
          <div className="topbar-brand-dot"></div>
          ARDI INVEST
          {isAdmin && <span className="admin-mode-badge">ADMIN</span>}
        </div>
        <div style={{ width: '120px', display: 'flex', justifyContent: 'flex-end' }}>
          {isAdmin && (
            <button className="admin-toggle-btn" onClick={() => setShowAdminPanel(true)}>
              📊 Dashboard
            </button>
          )}
        </div>
      </header>
      <main className="layout">
        <aside className="sidebar">
          <GeoAIChat 
            currentYear={debouncedYear} 
            currentIndex={activeFilter} 
            selectedLocation={selectedLocation}
            initialQuery={initialQuery}
            clearInitialQuery={() => setInitialQuery(null)}
          />
        </aside>
        <section className="map-area">
          <div className="toolbar">
            {/* Groundwater Dropdown */}
            <div 
              className="dropdown-container"
              onMouseEnter={handleMouseEnterGw}
              onMouseLeave={handleMouseLeaveGw}
            >
              <button
                type="button"
                className={`dropdown-trigger ${activeFilter === 'GWSA' || activeFilter === 'GWD' || activeFilter === 'Recharge' ? 'active' : ''}`}
                onClick={() => setGwDropdownOpen(!gwDropdownOpen)}
              >
                💧 Groundwater {activeFilter === 'GWSA' ? '· Storage' : activeFilter === 'GWD' ? '· Depth' : activeFilter === 'Recharge' ? '· Recharge' : ''} <span className="dropdown-chevron">▾</span>
              </button>
              {gwDropdownOpen && (
                <div className="dropdown-menu">
                  <button
                    type="button"
                    className={`dropdown-item ${activeFilter === 'GWSA' ? 'selected' : ''}`}
                    onClick={() => {
                      handleFilterChange('GWSA');
                      setGwDropdownOpen(false);
                    }}
                  >
                    💧 Storage Anomaly (GWSA)
                  </button>
                  <button
                    type="button"
                    className={`dropdown-item ${activeFilter === 'GWD' ? 'selected' : ''}`}
                    onClick={() => {
                      handleFilterChange('GWD');
                      setGwDropdownOpen(false);
                    }}
                  >
                    🕳️ Depth Change (GWD)
                  </button>
                  <button
                    type="button"
                    className={`dropdown-item ${activeFilter === 'Recharge' ? 'selected' : ''}`}
                    onClick={() => {
                      handleFilterChange('Recharge');
                      setGwDropdownOpen(false);
                    }}
                  >
                    🌧️ Recharge Rate (GWR)
                  </button>
                </div>
              )}
            </div>

            {/* Surface Water Dropdown */}
            <div 
              className="dropdown-container"
              onMouseEnter={handleMouseEnterSw}
              onMouseLeave={handleMouseLeaveSw}
            >
              <button
                type="button"
                className={`dropdown-trigger ${activeFilter === 'Surface Water' || activeFilter === 'Water Quantity' ? 'active' : ''}`}
                onClick={() => setSwDropdownOpen(!swDropdownOpen)}
              >
                🌊 Surface Water {activeFilter === 'Surface Water' ? '· NDWI' : activeFilter === 'Water Quantity' ? '· Quantity' : ''} <span className="dropdown-chevron">▾</span>
              </button>
              {swDropdownOpen && (
                <div className="dropdown-menu">
                  <button
                    type="button"
                    className={`dropdown-item ${activeFilter === 'Surface Water' ? 'selected' : ''}`}
                    onClick={() => {
                      handleFilterChange('Surface Water');
                      setSwDropdownOpen(false);
                    }}
                  >
                    🌊 Moisture Index (NDWI)
                  </button>
                  <button
                    type="button"
                    className={`dropdown-item ${activeFilter === 'Water Quantity' ? 'selected' : ''}`}
                    onClick={() => {
                      handleFilterChange('Water Quantity');
                      setSwDropdownOpen(false);
                    }}
                  >
                    💧 Water Quantity (SWQ)
                  </button>
                </div>
              )}
            </div>

            {/* Land Info Dropdown */}
            <div 
              className="dropdown-container"
              onMouseEnter={handleMouseEnterLand}
              onMouseLeave={handleMouseLeaveLand}
            >
              <button
                type="button"
                className={`dropdown-trigger ${activeFilter === 'Land Use' || activeFilter === 'Suitability' ? 'active' : ''}`}
                onClick={() => setLandDropdownOpen(!landDropdownOpen)}
              >
                🌍 Land Info {activeFilter === 'Land Use' ? '· Vegetation' : activeFilter === 'Suitability' ? '· Suitability' : ''} <span className="dropdown-chevron">▾</span>
              </button>
              {landDropdownOpen && (
                <div className="dropdown-menu">
                  <button
                    type="button"
                    className={`dropdown-item ${activeFilter === 'Land Use' ? 'selected' : ''}`}
                    onClick={() => {
                      handleFilterChange('Land Use');
                      setLandDropdownOpen(false);
                    }}
                  >
                    🌾 Vegetation Cover (NDVI)
                  </button>
                  <button
                    type="button"
                    className={`dropdown-item ${activeFilter === 'Suitability' ? 'selected' : ''}`}
                    onClick={() => {
                      handleFilterChange('Suitability');
                      setLandDropdownOpen(false);
                    }}
                  >
                    🚜 Land Suitability (LSI)
                  </button>
                </div>
              )}
            </div>
          </div>
          <div className="map-canvas">
            <MoroccoMap 
              selectedYear={debouncedYear} 
              activeFilter={activeFilter} 
              adminLevel={adminLevel} 
              inspector={selectedLocation}
              onInspect={setSelectedLocation}
            />
          </div>
        </section>
        <aside className="info-panel">
          <div className="year-section">
            <label>TEMPORAL RANGE</label>
            <div className="year-display">{selectedYear}</div>
            <input type="range" min={minYear} max={maxYear} step="1" value={selectedYear} onChange={(e) => setSelectedYear(parseInt(e.target.value))} />
          </div>
          <div className="panel-divider"></div>
          <div>
            <label>INSPECTION MODE</label>
            <div className="admin-buttons">
              <button
                onClick={() => setAdminLevel('admin0-all')}
                className={adminLevel === 'admin0-all' ? 'admin-btn active' : 'admin-btn'}>
                <span className="admin-icon">📍</span> Point Inspector
              </button>
              <button
                onClick={() => setAdminLevel('admin1-communes')}
                className={adminLevel === 'admin1-communes' ? 'admin-btn active' : 'admin-btn'}>
                <span className="admin-icon">🏡</span> Commune Level
              </button>
              <button
                onClick={() => setAdminLevel('admin2-regions')}
                className={adminLevel === 'admin2-regions' ? 'admin-btn active' : 'admin-btn'}>
                <span className="admin-icon">🗺️</span> Region Level
              </button>
            </div>
          </div>
        </aside>
      </main>

      {/* Admin Dashboard Overlay */}
      {isAdmin && (
        <AdminDashboard
          isOpen={showAdminPanel}
          onClose={() => setShowAdminPanel(false)}
        />
      )}
    </div>
  );
}

export default App;

