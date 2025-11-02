function EnginesDashboard({ engines }) {
  const mappers = engines.filter(e => e.role === 'mapper');
  const reducers = engines.filter(e => e.role === 'reducer');

  const getLoadPercentage = (engine) => {
    return (engine.current_load / engine.capacity) * 100;
  };

  const getStatusColor = (status) => {
    return status === 'active' ? 'engine-active' : 'engine-idle';
  };

  const renderEngine = (engine) => (
    <div key={engine.engine_id} className="engine-card" data-testid={`engine-${engine.engine_id}`}>
      <div className="engine-header">
        <div className="engine-id">{engine.engine_id}</div>
        <span className={`engine-status ${getStatusColor(engine.status)}`} data-testid={`engine-status-${engine.engine_id}`}>
          {engine.status}
        </span>
      </div>
      <div className="engine-capacity" data-testid={`engine-capacity-${engine.engine_id}`}>
        {engine.current_load} / {engine.capacity}
      </div>
      <div className="progress-bar">
        <div 
          className="progress-fill"
          style={{ width: `${getLoadPercentage(engine)}%` }}
          data-testid={`engine-load-${engine.engine_id}`}
        />
      </div>
    </div>
  );

  return (
    <div className="engines-dashboard-container" data-testid="engines-dashboard">
      <div className="card">
        <h2 className="card-title">Estado de los Engines</h2>
        
        {engines.length === 0 ? (
          <div className="empty-state" data-testid="empty-engines">
            <p>No hay Engines conectados</p>
            <p className="helper-text">Inicia los Engines con: python3 engine.py --engine-id mapper-1 --role mapper</p>
          </div>
        ) : (
          <>
            <div className="engines-section">
              <h3 className="section-title">Mapeadores ({mappers.length})</h3>
              <div className="engines-grid">
                {mappers.length === 0 ? (
                  <div className="empty-section" data-testid="empty-mappers">No hay mapeadores</div>
                ) : (
                  mappers.map(renderEngine)
                )}
              </div>
            </div>

            <div className="engines-section">
              <h3 className="section-title">Reductores ({reducers.length})</h3>
              <div className="engines-grid">
                {reducers.length === 0 ? (
                  <div className="empty-section" data-testid="empty-reducers">No hay reductores</div>
                ) : (
                  reducers.map(renderEngine)
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default EnginesDashboard;
