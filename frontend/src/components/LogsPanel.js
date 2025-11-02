import { useEffect, useRef } from 'react';

function LogsPanel({ logs }) {
  const logsEndRef = useRef(null);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  return (
    <div className="logs-panel-container" data-testid="logs-panel">
      <div className="card">
        <h2 className="card-title">Registros de Actividades</h2>
        
        <div className="logs-container">
          {logs.length === 0 ? (
            <div className="empty-state" data-testid="empty-logs">
              <p>Aún no hay actividades</p>
            </div>
          ) : (
            <>
              {logs.map((log, idx) => (
                <div key={idx} className="log-entry" data-testid={`log-${idx}`}>
                  <span className="log-time">{formatTime(log.timestamp)}</span>
                  <span className="log-message">{log.message}</span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default LogsPanel;
