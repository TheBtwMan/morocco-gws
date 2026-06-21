import { useState, useEffect, useCallback } from 'react';
import { getAdminStats, getAdminChatHistory } from '../services/apii.js';
import './AdminDashboard.css';

export default function AdminDashboard({ isOpen, onClose }) {
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [totalHistory, setTotalHistory] = useState(0);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [statsData, historyData] = await Promise.all([
        getAdminStats(),
        getAdminChatHistory(50, 0),
      ]);
      setStats(statsData);
      setHistory(historyData.history || []);
      setTotalHistory(historyData.total || 0);
    } catch (err) {
      console.error('Failed to fetch admin data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchData();
    }
  }, [isOpen, fetchData]);

  if (!isOpen) return null;

  const formatTimestamp = (ts) => {
    if (!ts) return '—';
    const d = new Date(ts);
    return d.toLocaleString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  };

  const truncate = (str, len = 80) => {
    if (!str) return '—';
    return str.length > len ? str.substring(0, len) + '…' : str;
  };

  // Calculate max for bar chart scaling
  const maxDayCount = stats?.queries_per_day?.length
    ? Math.max(...stats.queries_per_day.map(d => d.count), 1)
    : 1;

  return (
    <div className="admin-overlay" onClick={onClose}>
      <div className="admin-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="admin-panel-header">
          <div className="admin-panel-title-row">
            <div className="admin-panel-brand">
              <div className="admin-panel-dot" />
              <h2>Admin Dashboard</h2>
            </div>
            <button className="admin-close-btn" onClick={onClose}>✕</button>
          </div>
          <p className="admin-panel-subtitle">Platform usage analytics and research history</p>

          {/* Tabs */}
          <div className="admin-tabs">
            <button
              className={`admin-tab ${activeTab === 'overview' ? 'active' : ''}`}
              onClick={() => setActiveTab('overview')}
            >
              📊 Overview
            </button>
            <button
              className={`admin-tab ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
            >
              📋 Research History
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="admin-panel-content">
          {loading ? (
            <div className="admin-loading">
              <div className="admin-spinner" />
              <span>Loading analytics...</span>
            </div>
          ) : activeTab === 'overview' ? (
            /* ── Overview Tab ── */
            <div className="admin-overview">
              {/* Stat Cards */}
              <div className="admin-stat-cards">
                <div className="admin-stat-card">
                  <div className="admin-stat-icon">💬</div>
                  <div className="admin-stat-value">{stats?.total_queries || 0}</div>
                  <div className="admin-stat-label">Total Queries</div>
                </div>
                <div className="admin-stat-card">
                  <div className="admin-stat-icon">🗺️</div>
                  <div className="admin-stat-value">{stats?.top_regions?.length || 0}</div>
                  <div className="admin-stat-label">Regions Explored</div>
                </div>
                <div className="admin-stat-card">
                  <div className="admin-stat-icon">📊</div>
                  <div className="admin-stat-value">{stats?.top_indices?.length || 0}</div>
                  <div className="admin-stat-label">Indices Used</div>
                </div>
                <div className="admin-stat-card">
                  <div className="admin-stat-icon">📅</div>
                  <div className="admin-stat-value">{stats?.queries_per_day?.length || 0}</div>
                  <div className="admin-stat-label">Active Days</div>
                </div>
              </div>

              {/* Top Regions & Indices */}
              <div className="admin-two-col">
                <div className="admin-section-card">
                  <h3>🗺️ Top Queried Regions</h3>
                  {stats?.top_regions?.length > 0 ? (
                    <div className="admin-rank-list">
                      {stats.top_regions.map((r, i) => (
                        <div key={i} className="admin-rank-item">
                          <span className="admin-rank-num">#{i + 1}</span>
                          <span className="admin-rank-name">{r.name || 'Unknown'}</span>
                          <span className="admin-rank-count">{r.count} queries</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="admin-empty">No region data yet</div>
                  )}
                </div>

                <div className="admin-section-card">
                  <h3>📈 Top Used Indices</h3>
                  {stats?.top_indices?.length > 0 ? (
                    <div className="admin-rank-list">
                      {stats.top_indices.map((idx, i) => (
                        <div key={i} className="admin-rank-item">
                          <span className="admin-rank-num">#{i + 1}</span>
                          <span className="admin-rank-name">{idx.name || 'Unknown'}</span>
                          <span className="admin-rank-count">{idx.count} queries</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="admin-empty">No index data yet</div>
                  )}
                </div>
              </div>

              {/* Queries Per Day Chart */}
              <div className="admin-section-card full-width">
                <h3>📅 Queries Per Day</h3>
                {stats?.queries_per_day?.length > 0 ? (
                  <div className="admin-bar-chart">
                    {stats.queries_per_day.map((d, i) => (
                      <div key={i} className="admin-bar-col">
                        <div className="admin-bar-value">{d.count}</div>
                        <div
                          className="admin-bar"
                          style={{ height: `${(d.count / maxDayCount) * 100}%` }}
                        />
                        <div className="admin-bar-label">{d.date?.slice(5) || '—'}</div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="admin-empty">No daily data yet. Start using the chatbot!</div>
                )}
              </div>

              {/* Refresh */}
              <button className="admin-refresh-btn" onClick={fetchData}>
                🔄 Refresh Data
              </button>
            </div>
          ) : (
            /* ── History Tab ── */
            <div className="admin-history">
              <div className="admin-history-header">
                <span className="admin-history-count">
                  {totalHistory} total interaction{totalHistory !== 1 ? 's' : ''} recorded
                </span>
                <button className="admin-refresh-btn small" onClick={fetchData}>
                  🔄 Refresh
                </button>
              </div>

              {history.length > 0 ? (
                <div className="admin-history-table-wrap">
                  <table className="admin-history-table">
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>User Query</th>
                        <th>AI Response</th>
                        <th>Index</th>
                        <th>Region</th>
                      </tr>
                    </thead>
                    <tbody>
                      {history.map((entry, i) => (
                        <tr key={i}>
                          <td className="td-time">{formatTimestamp(entry.timestamp)}</td>
                          <td className="td-query">{truncate(entry.user_message, 60)}</td>
                          <td className="td-response">{truncate(entry.ai_response, 80)}</td>
                          <td className="td-index">
                            {entry.index ? (
                              <span className="admin-badge">{entry.index}</span>
                            ) : '—'}
                          </td>
                          <td className="td-region">
                            {entry.region ? (
                              <span className="admin-badge region-badge">{truncate(entry.region, 25)}</span>
                            ) : '—'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="admin-empty-history">
                  <div className="admin-empty-icon">📭</div>
                  <h4>No Research History Yet</h4>
                  <p>Chat interactions will appear here as users query the GeoAI advisor.</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
