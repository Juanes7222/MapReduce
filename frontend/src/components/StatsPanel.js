function StatsPanel({ stats }) {
  const statItems = [
    { label: 'Engines Totales', value: stats.total_engines, icon: '⚙️' },
    { label: 'Mapeadores', value: stats.mappers, icon: '🗺️' },
    { label: 'Reductores', value: stats.reducers, icon: '📊' },
    { label: 'Cola de Mapeo', value: stats.map_queue_size, icon: '📥' },
    { label: 'Cola de Reducción', value: stats.reduce_queue_size, icon: '📤' },
    { label: 'Trabajos Totales', value: stats.total_jobs, icon: '💼' },
    { label: 'Trabajos Activos', value: stats.active_jobs, icon: '🔄' },
  ];

  return (
    <div className="stats-panel-container" data-testid="stats-panel">
      <div className="card">
        <h2 className="card-title">Estadísticas del Sistema</h2>
        
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
