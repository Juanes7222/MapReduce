function JobsList({ jobs }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'map':
        return 'status-map';
      case 'shuffle':
        return 'status-shuffle';
      case 'reduce':
        return 'status-reduce';
      case 'completada':
        return 'status-done';
      default:
        return 'status-default';
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    return `${seconds.toFixed(2)}s`;
  };

  return (
    <div className="jobs-list-container" data-testid="jobs-list">
      <div className="card">
        <h2 className="card-title">Trabajos ({jobs.length})</h2>
        
        {jobs.length === 0 ? (
          <div className="empty-state" data-testid="empty-jobs">
            <p>Aún no hay trabajos. ¡Crea tu primer trabajo!</p>
          </div>
        ) : (
          <div className="jobs-grid">
            {jobs.slice().reverse().map((job) => (
              <div key={job.job_id} className="job-card" data-testid={`job-card-${job.job_id}`}>
                <div className="job-header">
                  <div>
                    <div className="job-id">{job.job_id.slice(0, 8)}</div>
                    <div className="job-meta">
                      {job.text_length} caracteres • {job.num_shards} shards
                    </div>
                  </div>
                  <span className={`status-badge ${getStatusColor(job.status)}`} data-testid={`job-status-${job.job_id}`}>
                    {job.status.toUpperCase()}
                  </span>
                </div>

                {job.status === 'completada' && job.top_words && (
                  <div className="job-results" data-testid={`job-results-${job.job_id}`}>
                    <div className="results-header">10 Palabras Más Frecuentes:</div>
                    <div className="words-grid">
                      {job.top_words.map((item, idx) => (
                        <div key={idx} className="word-item" data-testid={`word-${idx}`}>
                          <span className="word-text">{item.word}</span>
                          <span className="word-count">{item.count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="job-footer">
                  <div className="job-time">
                    {new Date(job.created_at).toLocaleTimeString()}
                  </div>
                  {job.duration_seconds && (
                    <div className="job-duration" data-testid={`job-duration-${job.job_id}`}>
                      {formatDuration(job.duration_seconds)}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default JobsList;
