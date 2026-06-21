import { useState, useEffect } from 'react';
import './RoleSelection.css';

const ADMIN_PASSWORD = 'admin123';

export default function RoleSelection({ onSelectUser, onSelectAdmin, onBack }) {
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState(false);
  const [shaking, setShaking] = useState(false);

  // Scroll-reveal animation
  useEffect(() => {
    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('revealed');
          }
        });
      },
      { threshold: 0.15 }
    );

    document.querySelectorAll('.role-reveal').forEach((el) => {
      revealObserver.observe(el);
    });

    return () => revealObserver.disconnect();
  }, []);

  const handleAdminSubmit = () => {
    if (password === ADMIN_PASSWORD) {
      setShowPasswordModal(false);
      setPassword('');
      setError(false);
      onSelectAdmin();
    } else {
      setError(true);
      setShaking(true);
      setTimeout(() => setShaking(false), 600);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleAdminSubmit();
    if (e.key === 'Escape') {
      setShowPasswordModal(false);
      setPassword('');
      setError(false);
    }
  };

  return (
    <div className="role-page">
      {/* Background effects */}
      <div className="role-particles">
        {[...Array(8)].map((_, i) => <div key={i} className="role-particle" />)}
      </div>
      <div className="role-orbit-ring role-ring-1" />
      <div className="role-orbit-ring role-ring-2" />

      {/* Back button */}
      <button className="role-back-btn" onClick={onBack}>
        <span className="role-back-arrow">←</span> Back to Home
      </button>

      {/* Header */}
      <div className="role-header role-reveal">
        <div className="role-badge">
          <span className="role-badge-dot" />
          ARDI INVEST PLATFORM
        </div>
        <h1>Select Your Access Level</h1>
        <p className="role-subtitle">
          Choose how you'd like to interact with the GeoAI platform. Users get full access to the interactive map and AI advisor. Administrators can additionally monitor platform usage and research history.
        </p>
      </div>

      {/* Role Cards */}
      <div className="role-cards role-reveal">
        {/* User Card */}
        <button className="role-card user-card" onClick={onSelectUser} id="role-user-btn">
          <div className="role-card-glow user-glow" />
          <div className="role-card-icon-wrap">
            <span className="role-card-icon">👤</span>
          </div>
          <h2>User</h2>
          <p>Access the interactive GeoAI platform with map exploration and AI-powered agricultural investment advisor.</p>
          <div className="role-card-features">
            <span className="role-feature">🗺️ Interactive Map</span>
            <span className="role-feature">🤖 AI Advisor</span>
            <span className="role-feature">📊 7 GEE Indices</span>
          </div>
          <div className="role-card-action">
            Enter Platform <span className="role-card-arrow">→</span>
          </div>
        </button>

        {/* Divider */}
        <div className="role-divider">
          <div className="role-divider-line" />
          <span className="role-divider-text">OR</span>
          <div className="role-divider-line" />
        </div>

        {/* Admin Card */}
        <button className="role-card admin-card" onClick={() => setShowPasswordModal(true)} id="role-admin-btn">
          <div className="role-card-glow admin-glow" />
          <div className="role-card-icon-wrap admin-icon-wrap">
            <span className="role-card-icon">🔐</span>
          </div>
          <h2>Administrator</h2>
          <p>Full platform access plus a dashboard showing research history, chat logs, and usage analytics.</p>
          <div className="role-card-features">
            <span className="role-feature admin-feature">📋 Research History</span>
            <span className="role-feature admin-feature">📈 Usage Statistics</span>
            <span className="role-feature admin-feature">🔍 Chat Logs</span>
          </div>
          <div className="role-card-action admin-action">
            Authenticate <span className="role-card-arrow">→</span>
          </div>
        </button>
      </div>

      {/* Password Modal */}
      {showPasswordModal && (
        <div className="role-modal-overlay" onClick={() => { setShowPasswordModal(false); setPassword(''); setError(false); }}>
          <div className={`role-modal ${shaking ? 'shake' : ''}`} onClick={(e) => e.stopPropagation()}>
            <div className="role-modal-header">
              <div className="role-modal-icon">🔐</div>
              <h3>Administrator Access</h3>
              <p>Enter the admin password to access the dashboard with research history and usage analytics.</p>
            </div>

            <div className="role-modal-body">
              <label className="role-modal-label">Password</label>
              <div className={`role-modal-input-wrap ${error ? 'error' : ''}`}>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setError(false); }}
                  onKeyDown={handleKeyDown}
                  placeholder="Enter admin password..."
                  autoFocus
                  id="admin-password-input"
                />
              </div>
              {error && (
                <div className="role-modal-error">
                  <span>⚠️</span> Incorrect password. Please try again.
                </div>
              )}
            </div>

            <div className="role-modal-actions">
              <button className="role-modal-cancel" onClick={() => { setShowPasswordModal(false); setPassword(''); setError(false); }}>
                Cancel
              </button>
              <button className="role-modal-submit" onClick={handleAdminSubmit} disabled={!password.trim()} id="admin-submit-btn">
                Authenticate →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
