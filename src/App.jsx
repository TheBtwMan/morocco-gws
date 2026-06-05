import { useState, useEffect, useRef } from 'react';
import MoroccoMap from './components/Map/MoroccoMap.jsx';
import { postChatQuery, preloadAllPlatformData } from './services/apii.js';
import LandingPage from './components/LandingPage.jsx';
import './App.css';

function GeoAIChat({ currentYear, currentIndex, initialQuery, clearInitialQuery }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `### 👋 Welcome to the GeoAI Resource & Investment Advisor!

I am your intelligent assistant linked directly to **Google Earth Engine (GEE)**. I analyze soil, surface moisture, and deep aquifers in Morocco to help you make climate-resilient investment decisions.

#### 💡 How to Interact with Me:
1.  **Ask about a specific region**: Type something like *"Can I invest in Souss-Massa?"* or *"Analyze Marrakech-Safi"*.
2.  **Learn about scientific indices**: Ask *"What is NDWI?"*, *"Explain NDVI"*, or *"How is groundwater measured?"*.
3.  **Use Active Map Context**: Check **"Sync Map Context"** below. When enabled, asking *"Is it safe to invest here?"* will automatically analyze the active region, year, and index currently selected on your map view!

*Select a preset question pill below or type your custom query to begin!*`
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [syncMapContext, setSyncMapContext] = useState(true);
  
  const chatMessagesRef = useRef(null);

  // Auto-scroll to bottom of chat without shifting the page viewport
  useEffect(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

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
    { label: "🌊 Explain NDWI water index", text: "Explain the NDWI surface water index and what it tells us." }
  ];

  const handleSend = async (text) => {
    if (!text || text.trim() === '') return;
    
    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsLoading(true);

    try {
      const context = syncMapContext ? {
        year: currentYear,
        index: currentIndex
      } : {};
      
      const history = messages.slice(-10); // send last 10 messages for history context

      const response = await postChatQuery(text, history, context);
      
      setMessages(prev => [...prev, { role: 'assistant', content: response }]);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `⚠️ **Connection Error**: Failed to reach the GeoAI service. Please make sure the FastAPI server is running at http://localhost:8000.`
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleSend(inputValue);
    }
  };

  function parseInlineMarkdown(text) {
    if (!text) return "";
    const parts = text.split(/(\*\*.*?\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        const rawText = part.substring(2, part.length - 2);
        if (rawText.includes("HIGH RISK") || rawText.includes("Severe")) {
          return <span key={i} className="risk-badge badge-red">{rawText}</span>;
        } else if (rawText.includes("MODERATE RISK") || rawText.includes("Moderate")) {
          return <span key={i} className="risk-badge badge-yellow">{rawText}</span>;
        } else if (rawText.includes("HIGH VIABILITY") || rawText.includes("Stable") || rawText.includes("Excellent")) {
          return <span key={i} className="risk-badge badge-green">{rawText}</span>;
        }
        return <strong key={i} style={{ color: '#7BD4E9', fontWeight: 'bold' }}>{rawText}</strong>;
      }
      return part;
    });
  }

  function renderMarkdown(text) {
    if (!text) return null;
    const lines = text.split('\n');
    return lines.map((line, idx) => {
      const trimmed = line.trim();
      if (!trimmed) return <div key={idx} style={{ height: '6px' }} />;
      if (trimmed === '---') return <hr key={idx} style={{ border: 0, height: '1px', background: '#313142', margin: '8px 0' }} />;
      
      if (trimmed.startsWith('### ')) {
        return <h3 key={idx}>{trimmed.substring(4)}</h3>;
      }
      if (trimmed.startsWith('#### ')) {
        return <h4 key={idx}>{trimmed.substring(5)}</h4>;
      }
      
      if (trimmed.startsWith('>')) {
        let quoteText = trimmed.substring(1).trim();
        let alertStyle = {};
        if (quoteText.startsWith('[!WARNING]')) {
          quoteText = quoteText.replace('[!WARNING]', '').trim();
          alertStyle = { borderLeft: '3px solid #ef4444', background: 'rgba(239, 68, 68, 0.1)', padding: '4px 8px', margin: '4px 0' };
        } else if (quoteText.startsWith('[!IMPORTANT]')) {
          quoteText = quoteText.replace('[!IMPORTANT]', '').trim();
          alertStyle = { borderLeft: '3px solid #f59e0b', background: 'rgba(245, 158, 11, 0.1)', padding: '4px 8px', margin: '4px 0' };
        } else if (quoteText.startsWith('[!TIP]')) {
          quoteText = quoteText.replace('[!TIP]', '').trim();
          alertStyle = { borderLeft: '3px solid #10b981', background: 'rgba(16, 185, 129, 0.1)', padding: '4px 8px', margin: '4px 0' };
        }
        return (
          <blockquote key={idx} style={alertStyle}>
            {parseInlineMarkdown(quoteText)}
          </blockquote>
        );
      }
      
      if (trimmed.startsWith('* ') || trimmed.startsWith('- ')) {
        return (
          <ul key={idx} style={{ margin: '3px 0 3px 14px', paddingLeft: 0 }}>
            <li style={{ listStyleType: 'disc', fontSize: '12px' }}>
              {parseInlineMarkdown(trimmed.substring(2))}
            </li>
          </ul>
        );
      }
      
      return <p key={idx} style={{ margin: '0 0 6px 0' }}>{parseInlineMarkdown(trimmed)}</p>;
    });
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-indicator"></div>
        <h3>GeoAI Advisor</h3>
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
            {msg.role === 'assistant' ? renderMarkdown(msg.content) : msg.content}
          </div>
        ))}
        {isLoading && (
          <div className="chat-loading">
            <span className="dot"></span>
            <span className="dot"></span>
            <span className="dot"></span>
          </div>
        )}
      </div>

      <div className="chat-presets">
        <span className="chat-presets-title">Quick Inquiries</span>
        <div className="preset-pills">
          {presetPrompts.map((p, i) => (
            <button 
              key={i} 
              className="preset-pill" 
              onClick={() => handleSend(p.text)}
              disabled={isLoading}
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
          disabled={isLoading}
        />
        <button 
          className="chat-send-btn" 
          onClick={() => handleSend(inputValue)}
          disabled={isLoading || !inputValue.trim()}
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

  const [activeFilter, setActiveFilter] = useState('Groundwater');
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
    setView('platform');
  };

  if (view === 'landing') {
    return <LandingPage onLaunch={handleLaunchPlatform} />;
  }

  return (
    <div className="platform">
      <header className="topbar">
        <button className="back-hub-btn" onClick={() => setView('landing')}>
          ← Marketing Page
        </button>
        <span>PLATEFORME GeoAI</span>
        <div style={{ width: '100px' }}></div>
      </header>
      <main className="layout">
        <aside className="sidebar">
          <GeoAIChat 
            currentYear={debouncedYear} 
            currentIndex={activeFilter} 
            initialQuery={initialQuery}
            clearInitialQuery={() => setInitialQuery(null)}
          />
        </aside>
        <section className="map-area">
          <div className="toolbar">
            <button
              onClick={() => handleFilterChange('Groundwater')}
              className={activeFilter === 'Groundwater' ? 'active' : ''}>
              Groundwater
            </button>
            <button
              onClick={() => handleFilterChange('Surface Water')}
              className={activeFilter === 'Surface Water' ? 'active' : ''}>
              Surface Water
            </button>
            <button
              onClick={() => handleFilterChange('Land Use')}
              className={activeFilter === 'Land Use' ? 'active' : ''}>
              Land Use
            </button>

          </div>
          <div className="map-canvas">
            <MoroccoMap selectedYear={debouncedYear} activeFilter={activeFilter} adminLevel={adminLevel} />
          </div>
        </section>
        <aside className="info-panel">
          <div>
            <label>YEAR</label>
            <input type="range" min={minYear} max={maxYear} step="1" value={selectedYear} onChange={(e) => setSelectedYear(parseInt(e.target.value))} />
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

