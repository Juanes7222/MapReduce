function StatsPanel({ stats }) {
  const statItems = [
    { label: 'Total Engines', value: stats.total_engines, icon: '⚙️' },
    { label: 'Mappers', value: stats.mappers, icon: '🗺️' },
    { label: 'Reducers', value: stats.reducers, icon: '📊' },
    { label: 'Map Queue', value: stats.map_queue_size, icon: '📥' },
    { label: 'Reduce Queue', value: stats.reduce_queue_size, icon: '📤' },
    { label: 'Total Jobs', value: stats.total_jobs, icon: '💼' },
    { label: 'Active Jobs', value: stats.active_jobs, icon: '🔄' },
  ];

  return (
    <div className="stats-panel-container" data-testid="stats-panel">
      <div className="card">
        <h2 className="card-title">System Statistics</h2>
        
        <div className="stats-grid">
          {statItems.map((item, idx) => (
            <div key={idx} className="stat-item" data-testid={`stat-${item.label.toLowerCase().replace(' ', '-')}`}>
              <div className="stat-icon">{item.icon}</div>
              <div className="stat-content">
                <div className="stat-value">{item.value}</div>
                <div className="stat-label">{item.label}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default StatsPanel;
