import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [state, setState] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [viewMode, setViewMode] = useState('desktop'); // 'desktop', 'mobile', or 'reaction_studio'
  const [selectedEmail, setSelectedEmail] = useState(null);
  const [activeTab, setActiveTab] = useState('billing'); // 'billing', 'email', 'sms', 'push'
  const [loading, setLoading] = useState(true);
  const [pollError, setPollError] = useState(false);
  const [customerActionNote, setCustomerActionNote] = useState('');

  // Poll state.json from Streamlit export
  useEffect(() => {
    const fetchState = () => {
      fetch('/state.json')
        .then((res) => {
          if (!res.ok) throw new Error('State not initialized');
          return res.json();
        })
        .then((data) => {
          setState(data);
          setLoading(false);
          setPollError(false);
          
          if (currentUser) {
            const updatedUser = data.customers.find((c) => c.id === currentUser.id);
            if (updatedUser) {
              setCurrentUser(updatedUser);
            }
          }
        })
        .catch((err) => {
          setPollError(true);
          setLoading(false);
        });
    };

    fetchState();
    const interval = setInterval(fetchState, 2000);
    return () => clearInterval(interval);
  }, [currentUser]);

  // Fallback initial personas
  const defaultCustomers = [
    { id: "C001", name: "Student Sam", persona: "Price-sensitive student with exam drop-offs", product_id: "P001", status: "Active", engagement_score: 85, segment: "Price-Sensitive", clv: 29.0 },
    { id: "C002", name: "Corporate Clara", persona: "Busy technical manager requiring API value", product_id: "P002", status: "Active", engagement_score: 40, segment: "High-Value", clv: 99.0 },
    { id: "C003", name: "Ghosting Greg", persona: "Silent developer with high churn probability", product_id: "P003", status: "Active", engagement_score: 25, segment: "Churn-Risk", clv: 15.0 },
    { id: "C004", name: "Scale-up Sarah", persona: "SaaS founder hitting webhook and usage limits", product_id: "P001", status: "Active", engagement_score: 90, segment: "Upsell Candidate", clv: 29.0 },
    { id: "C005", name: "Bargain Betty", persona: "Deal hunter only reactive to heavy promotions", product_id: "P001", status: "Active", engagement_score: 30, segment: "Price-Sensitive", clv: 29.0 }
  ];

  const productCatalog = {
    "P001": { name: "Pro Subscription", base_price: 29.0, desc: "Unlimited workspaces, standard API rate limits" },
    "P002": { name: "Enterprise Plan", base_price: 99.0, desc: "SAML SSO, 24/7 dedicated support, SLA compliance" },
    "P003": { name: "API Add-on", base_price: 15.0, desc: "High-throughput API usage keys and priority queue" },
    "P004": { name: "Pro + API Bundle", base_price: 39.0, desc: "Combined Pro tier and high-throughput query bundle" }
  };

  const customersList = state ? state.customers : defaultCustomers;

  const handleLogin = (user) => {
    setCurrentUser(user);
    setSelectedEmail(null);
    setActiveTab('billing');
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setCustomerActionNote('');
  };

  // Filter messages for logged-in user
  const userMessages = currentUser && currentUser.messages ? currentUser.messages : [];
  const emails = userMessages.filter(m => m.channel === 'Email');
  const sms = userMessages.filter(m => m.channel === 'SMS');
  const push = userMessages.filter(m => m.channel === 'Push');

  const productKey = currentUser ? (currentUser.product_id || 'P001') : 'P001';
  const currentProduct = productCatalog[productKey] || productCatalog['P001'];
  const basePrice = state && state.price_history && state.price_history[currentProduct.name]
    ? state.price_history[currentProduct.name].slice(-1)[0]
    : currentProduct.base_price;

  const hasActiveDiscount = currentUser && 
    (currentUser.last_action === 'SEND_SMS_DISCOUNT' || currentUser.last_action === 'SEND_EMAIL_DISCOUNT');
  const discountRate = hasActiveDiscount ? 0.3 : 0.0;
  const finalPrice = (basePrice * (1 - discountRate)).toFixed(2);

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100vh', gap: '1rem' }}>
        <div style={{ width: '40px', height: '40px', border: '3px solid rgba(99,102,241,0.2)', borderLeftColor: '#6366f1', borderRadius: '50%', animation: 'spin 1s linear infinite' }}></div>
        <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>Initializing Client Workspace...</p>
      </div>
    );
  }

  // ─────────────────────────────────────────────
  // 1. PERSONA LOGIN SCREEN (BENTO GRID)
  // ─────────────────────────────────────────────
  if (!currentUser) {
    return (
      <div className="login-wrapper">
        <div className="login-card-container">
          <div className="login-header-section">
            <span className="brand-badge">⚡ RetentionX Client Portal</span>
            <h1>Customer Perspective Workspace</h1>
            <p>Select any simulated customer persona to view their private inbox, inspect personalized pricing discounts offered by the autonomous agent, and test interactive responses.</p>
          </div>

          {pollError && (
            <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.3)', color: '#fcd34d', padding: '0.8rem 1.2rem', borderRadius: '12px', marginBottom: '1.5rem', fontSize: '0.9rem', textAlign: 'center' }}>
              💡 <strong>Streamlit Offline / Idle:</strong> Run <code>python -m streamlit run app.py</code> in the root terminal to enable live two-way agent synchronization. Showing cached state.
            </div>
          )}

          <div className="bento-user-grid">
            {customersList.map((user) => {
              const prod = productCatalog[user.product_id || 'P001'] || productCatalog['P001'];
              const isChurned = user.status === 'Churned';
              const score = user.engagement_score || 0;
              const healthColor = score < 30 ? '#f43f5e' : score < 70 ? '#f59e0b' : '#10b981';

              return (
                <div 
                  key={user.id} 
                  className={`user-bento-card ${isChurned ? 'churned' : ''}`}
                  onClick={() => !isChurned && handleLogin(user)}
                >
                  <div className="card-top-row">
                    <div className="avatar-sphere">
                      {user.name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <span className="tag-pill">{user.segment || 'Customer'}</span>
                  </div>

                  <h3>{user.name}</h3>
                  <div className="user-bento-persona">{user.persona}</div>

                  <div className="bento-metrics-row">
                    <span style={{ color: '#94a3b8' }}>Engagement</span>
                    <strong style={{ color: healthColor }}>{score}/100</strong>
                  </div>
                  <div className="bento-health-bar">
                    <div className="bento-health-fill" style={{ width: `${score}%`, backgroundColor: healthColor }}></div>
                  </div>

                  <div className="bento-metrics-row" style={{ marginBottom: '1rem' }}>
                    <span style={{ color: '#94a3b8' }}>Plan</span>
                    <strong style={{ color: '#cbd5e1' }}>{prod.name}</strong>
                  </div>

                  {isChurned ? (
                    <div style={{ textAlign: 'center', fontSize: '0.75rem', color: '#f43f5e', fontWeight: 700, padding: '0.4rem' }}>
                      💀 CHURNED (Unsubscribed)
                    </div>
                  ) : (
                    <button className="bento-login-btn">
                      Log In as {user.name.split(' ')[0]} →
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  // ─────────────────────────────────────────────
  // 2. MAIN WORKSPACE VIEW
  // ─────────────────────────────────────────────
  return (
    <div className="workspace-wrapper">
      {/* Top Navbar */}
      <header className="portal-navbar">
        <div className="nav-brand-group">
          <span className="nav-logo">⚡ RetentionX Client Portal</span>
          <div className="live-badge">
            <span className="pulse-dot"></span>
            <span>Live Loop Connected</span>
          </div>
        </div>

        <div className="nav-user-actions">
          <div className="view-switcher">
            <button 
              className={`view-switcher-btn ${viewMode === 'desktop' ? 'active' : ''}`}
              onClick={() => setViewMode('desktop')}
            >
              💻 Desktop
            </button>
            <button 
              className={`view-switcher-btn ${viewMode === 'mobile' ? 'active' : ''}`}
              onClick={() => setViewMode('mobile')}
            >
              📱 Mobile
            </button>
            <button 
              className={`view-switcher-btn ${viewMode === 'reaction_studio' ? 'active' : ''}`}
              onClick={() => setViewMode('reaction_studio')}
            >
              ⚡ Action Studio
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            <span style={{ fontSize: '0.82rem', color: '#cbd5e1', fontWeight: 600 }}>
              {currentUser.name}
            </span>
            <button className="logout-outline-btn" onClick={handleLogout}>Switch User</button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      {viewMode === 'desktop' && (
        <div className="portal-main-layout">
          {/* Left Navigation */}
          <aside className="portal-sidebar">
            <nav className="portal-nav-stack">
              <button 
                className={`nav-tab-button ${activeTab === 'billing' ? 'active' : ''}`}
                onClick={() => setActiveTab('billing')}
              >
                <span>💳 Plan & Invoices</span>
              </button>
              <button 
                className={`nav-tab-button ${activeTab === 'email' ? 'active' : ''}`}
                onClick={() => setActiveTab('email')}
              >
                <span>✉️ Mailbox</span>
                {emails.length > 0 && <span className="nav-pill-count">{emails.length}</span>}
              </button>
              <button 
                className={`nav-tab-button ${activeTab === 'sms' ? 'active' : ''}`}
                onClick={() => setActiveTab('sms')}
              >
                <span>💬 SMS Transcripts</span>
                {sms.length > 0 && <span className="nav-pill-count">{sms.length}</span>}
              </button>
              <button 
                className={`nav-tab-button ${activeTab === 'push' ? 'active' : ''}`}
                onClick={() => setActiveTab('push')}
              >
                <span>🔔 Push Notices</span>
                {push.length > 0 && <span className="nav-pill-count">{push.length}</span>}
              </button>
            </nav>

            <div className="user-status-card">
              <h4>Telemetry Snapshot</h4>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.4rem' }}>
                <span style={{ color: '#94a3b8' }}>Health Score</span>
                <strong>{currentUser.engagement_score}/100</strong>
              </div>
              <div className="bento-health-bar" style={{ marginBottom: '0.8rem' }}>
                <div 
                  className="bento-health-fill" 
                  style={{ 
                    width: `${currentUser.engagement_score}%`, 
                    backgroundColor: currentUser.engagement_score < 30 ? '#f43f5e' : currentUser.engagement_score < 70 ? '#f59e0b' : '#10b981' 
                  }}
                ></div>
              </div>
              <div style={{ fontSize: '0.75rem', color: '#94a3b8', lineHeight: 1.5 }}>
                <div>⏱️ <strong>Inactivity:</strong> {currentUser.time_since_last_event || 0} days</div>
                <div>🏷️ <strong>Segment:</strong> {currentUser.segment}</div>
                <div>💵 <strong>Estimated CLV:</strong> ${(currentUser.clv || 0).toFixed(2)}</div>
              </div>
            </div>
          </aside>

          {/* Right Content */}
          <main className="portal-content-body">
            {/* BILLING TAB */}
            {activeTab === 'billing' && (
              <div>
                <h2 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '0.4rem', color: '#fff' }}>Subscription Workspace</h2>
                <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1.5rem' }}>Review current tier rates, personalized retention discounts, and billing status.</p>

                <div className="billing-hero-grid">
                  <div className="plan-spotlight-card">
                    {hasActiveDiscount && (
                      <div className="discount-ribbon">
                        ⚡ 30% Promo Activated by Autonomous Agent
                      </div>
                    )}
                    <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#a5b4fc', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Active Subscription</span>
                    <h3 style={{ fontSize: '1.8rem', color: '#fff', margin: '0.4rem 0' }}>{currentProduct.name}</h3>
                    <p style={{ color: '#cbd5e1', fontSize: '0.88rem' }}>{currentProduct.desc}</p>

                    <div className="big-price-display">
                      <span className="price-main">${finalPrice}</span>
                      {hasActiveDiscount && <span className="price-old">${basePrice.toFixed(2)}</span>}
                      <span className="price-sub">/ month</span>
                    </div>

                    <button 
                      className="glow-btn"
                      onClick={() => setCustomerActionNote(`Renewed ${currentProduct.name} at $${finalPrice}/mo.`)}
                    >
                      {hasActiveDiscount ? 'Claim 30% Promo & Renew' : 'Renew Subscription'}
                    </button>
                  </div>

                  <div className="glass-panel" style={{ padding: '1.75rem' }}>
                    <h3 style={{ fontSize: '1.1rem', color: '#fff', marginBottom: '1rem' }}>Pricing Breakdown</h3>
                    <div className="breakdown-row">
                      <span style={{ color: '#94a3b8' }}>Standard Base Price</span>
                      <span>${basePrice.toFixed(2)}</span>
                    </div>
                    <div className="breakdown-row">
                      <span style={{ color: '#94a3b8' }}>Agent Retention Promo</span>
                      <span style={{ color: hasActiveDiscount ? '#10b981' : '#94a3b8' }}>
                        {hasActiveDiscount ? '- 30% ($' + (basePrice * 0.3).toFixed(2) + ')' : '$0.00'}
                      </span>
                    </div>
                    <div className="breakdown-row total-row">
                      <span>Total Invoice</span>
                      <span style={{ color: '#38bdf8' }}>${finalPrice}/mo</span>
                    </div>

                    {customerActionNote && (
                      <div style={{ marginTop: '1rem', padding: '0.6rem 0.8rem', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.1)', color: '#6ee7b7', fontSize: '0.8rem' }}>
                        ✓ {customerActionNote}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* EMAIL TAB */}
            {activeTab === 'email' && (
              <div>
                <h2 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '0.4rem', color: '#fff' }}>Mailbox Client</h2>
                <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1.5rem' }}>Inspect retention emails dispatched by the agent.</p>

                {emails.length === 0 ? (
                  <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
                    ✉️ No emails delivered yet. When the agent schedules an email campaign, it will arrive here.
                  </div>
                ) : (
                  <div className="inbox-split-view">
                    <div className="inbox-list-pane">
                      {emails.map((e, idx) => (
                        <div 
                          key={idx} 
                          className={`email-row-item ${selectedEmail === e ? 'active' : ''}`}
                          onClick={() => setSelectedEmail(e)}
                        >
                          <div style={{ fontWeight: 700, color: '#fff', fontSize: '0.88rem', marginBottom: '0.2rem' }}>
                            {e.content.split('\n')[0].replace('Subject: ', '')}
                          </div>
                          <div style={{ color: '#94a3b8', fontSize: '0.78rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {e.content.split('\n').slice(2).join(' ')}
                          </div>
                          <div style={{ fontSize: '0.7rem', color: '#6366f1', marginTop: '0.4rem', fontWeight: 600 }}>
                            Delivered Day {e.day}
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="inbox-reader-pane">
                      {selectedEmail ? (
                        <>
                          <div className="reader-header">
                            <h3 style={{ fontSize: '1.25rem', color: '#fff', marginBottom: '0.5rem' }}>
                              {selectedEmail.content.split('\n')[0].replace('Subject: ', '')}
                            </h3>
                            <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                              From: <strong style={{ color: '#e2e8f0' }}>RetentionX AI Team &lt;retention@saas.ai&gt;</strong> • Day {selectedEmail.day}
                            </div>
                          </div>
                          <div className="reader-body">
                            {selectedEmail.content.split('\n').slice(2).join('\n')}
                          </div>
                          <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.08)', fontSize: '0.82rem', color: '#38bdf8' }}>
                            🤝 <strong>Simulated Customer Response:</strong> {selectedEmail.reaction} (Impact: +{selectedEmail.impact})
                          </div>
                        </>
                      ) : (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#64748b' }}>
                          Select an email from the left pane to view its full text.
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* SMS TAB */}
            {activeTab === 'sms' && (
              <div>
                <h2 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '0.4rem', color: '#fff' }}>Cellular SMS Logs</h2>
                <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1.5rem' }}>High-urgency mobile SMS alerts delivered directly to device.</p>

                {sms.length === 0 ? (
                  <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
                    💬 No SMS alerts dispatched yet.
                  </div>
                ) : (
                  <div className="sms-stream-container">
                    {sms.map((s, idx) => (
                      <div key={idx} className="sms-bubble-card">
                        <div className="bubble-carrier-tag">Cellular SMS • Day {s.day}</div>
                        <div className="bubble-message-text">{s.content}</div>
                        <div style={{ fontSize: '0.8rem', color: '#a5b4fc' }}>
                          📱 <strong>Simulated Reaction:</strong> {s.reaction}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* PUSH TAB */}
            {activeTab === 'push' && (
              <div>
                <h2 style={{ fontSize: '1.6rem', fontWeight: 800, marginBottom: '0.4rem', color: '#fff' }}>Push Notification Trays</h2>
                <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1.5rem' }}>In-app and mobile lockscreen notifications.</p>

                {push.length === 0 ? (
                  <div className="glass-panel" style={{ padding: '3rem', textAlign: 'center', color: '#94a3b8' }}>
                    🔔 No push notifications dispatched yet.
                  </div>
                ) : (
                  <div style={{ display: 'grid', gap: '1rem', maxWidth: '680px' }}>
                    {push.map((p, idx) => (
                      <div key={idx} className="glass-panel" style={{ padding: '1.25rem' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#f59e0b', fontWeight: 700, marginBottom: '0.4rem' }}>
                          <span>🔔 SYSTEM NOTIFICATION</span>
                          <span>Day {p.day}</span>
                        </div>
                        <div style={{ fontSize: '0.95rem', color: '#fff', marginBottom: '0.5rem' }}>{p.content}</div>
                        <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Outcome: {p.reaction}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </main>
        </div>
      )}

      {/* MOBILE DEVICE SIMULATOR */}
      {viewMode === 'mobile' && (
        <div className="mobile-simulator-stage">
          <div className="phone-hardware">
            <div className="island-notch"></div>
            <div className="phone-screen-content">
              <div style={{ textAlign: 'center', fontSize: '0.75rem', color: '#94a3b8' }}>
                Simulator: {currentUser.name}
              </div>

              {userMessages.length > 0 ? (
                userMessages.map((m, idx) => (
                  <div key={idx} className="lockscreen-notif">
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#93c5fd', fontWeight: 700, marginBottom: '0.3rem' }}>
                      <span>{m.channel === 'SMS' ? '💬 Messages' : m.channel === 'Email' ? '✉️ Mail' : '🔔 Alert'}</span>
                      <span>Day {m.day}</span>
                    </div>
                    <div style={{ fontSize: '0.82rem', lineHeight: 1.4 }}>
                      {m.channel === 'Email' ? m.content.split('\n')[0] : m.content}
                    </div>
                  </div>
                ))
              ) : (
                <div style={{ textAlign: 'center', color: '#64748b', fontSize: '0.8rem', marginTop: '4rem' }}>
                  No incoming alerts on device.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* INTERACTIVE CUSTOMER ACTION STUDIO */}
      {viewMode === 'reaction_studio' && (
        <div style={{ maxWidth: '800px', margin: '2rem auto', padding: '0 1rem' }}>
          <div className="glass-panel" style={{ padding: '2rem' }}>
            <h2 style={{ fontSize: '1.6rem', color: '#fff', marginBottom: '0.5rem' }}>⚡ Customer Reaction Studio</h2>
            <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
              Simulate manual customer responses to test how the autonomous agent adapts its strategies.
            </p>

            <div style={{ display: 'grid', gap: '1rem' }}>
              <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px' }}>
                <h4 style={{ color: '#fff', marginBottom: '0.4rem' }}>🎟️ Promo Code Acceptance</h4>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.8rem' }}>Customer clicks link and applies promotional code.</p>
                <button 
                  className="glow-btn"
                  onClick={() => setCustomerActionNote('Successfully applied code SAVEMORE30. Renewal price locked at 30% discount.')}
                >
                  Accept Discount Offer
                </button>
              </div>

              <div style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)', borderRadius: '12px' }}>
                <h4 style={{ color: '#fff', marginBottom: '0.4rem' }}>🛑 Opt-Out of SMS</h4>
                <p style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: '0.8rem' }}>User replies STOP to outreach message.</p>
                <button 
                  style={{ background: 'rgba(244, 63, 94, 0.2)', border: '1px solid #f43f5e', color: '#f43f5e', padding: '0.55rem 1.2rem', borderRadius: '8px', cursor: 'pointer', fontWeight: 600 }}
                  onClick={() => setCustomerActionNote('Replied STOP: Customer opted out from further SMS notifications.')}
                >
                  Reply STOP
                </button>
              </div>
            </div>

            {customerActionNote && (
              <div style={{ marginTop: '1.5rem', padding: '0.8rem 1rem', background: 'rgba(99, 102, 241, 0.15)', border: '1px solid rgba(99, 102, 241, 0.3)', borderRadius: '10px', color: '#c7d2fe' }}>
                ✓ {customerActionNote}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
