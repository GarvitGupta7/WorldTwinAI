import React from 'react';

export const Navbar = ({ currentView, onSelectView, systemHealth }) => {
  const views = [
    { id: 'living-world', label: 'Living World' },
    { id: 'scenario-studio', label: 'Scenario Studio' },
    { id: 'future-branches', label: 'Future Branches' },
    { id: 'experiment-lab', label: 'Experiment Lab' },
    { id: 'ai-copilot', label: 'AI Copilot' },
    { id: 'intervention-lab', label: 'Intervention Lab' },
    { id: 'knowledge-graph', label: 'Knowledge Graph' },
    { id: 'research-reports', label: 'Research Reports' },
  ];

  return (
    <header className="navbar-container">
      <div className="navbar-brand">
        <div className="brand-logo-badge">WT</div>
        <div className="brand-titles">
          <span className="brand-name">WorldTwin AI</span>
          <span className="brand-sub">Generative Digital Twin Platform</span>
        </div>
      </div>

      <nav className="navbar-links">
        {views.map(v => (
          <button
            key={v.id}
            className={`nav-tab-btn ${currentView === v.id ? 'active' : ''}`}
            onClick={() => onSelectView(v.id)}
          >
            {v.label}
          </button>
        ))}
      </nav>

      <div className="navbar-status">
        <span className={`status-indicator ${systemHealth === 'healthy' ? 'online' : 'warn'}`} />
        <span className="status-text">{(systemHealth || 'OK').toUpperCase()}</span>
      </div>
    </header>
  );
};
