import { useState, useEffect } from 'react';
import '@/App.css';
import axios from 'axios';
import JobForm from './components/JobForm';
import JobsList from './components/JobsList';
import EnginesDashboard from './components/EnginesDashboard';
import LogsPanel from './components/LogsPanel';
import StatsPanel from './components/StatsPanel';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [jobs, setJobs] = useState([]);
  const [engines, setEngines] = useState([]);
  const [logs, setLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Polling interval (1 second)
  useEffect(() => {
    const interval = setInterval(() => {
      fetchJobs();
      fetchEngines();
      fetchLogs();
      fetchStats();
    }, 1000);

    // Initial fetch
    fetchJobs();
    fetchEngines();
    fetchLogs();
    fetchStats();

    return () => clearInterval(interval);
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await axios.get(`${API}/jobs`);
      setJobs(response.data);
    } catch (error) {
      console.error('Error fetching jobs:', error);
    }
  };

  const fetchEngines = async () => {
    try {
      const response = await axios.get(`${API}/engines`);
      setEngines(response.data);
    } catch (error) {
      console.error('Error fetching engines:', error);
    }
  };

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API}/logs`);
      setLogs(response.data);
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await axios.get(`${API}/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handleJobCreated = () => {
    fetchJobs();
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <div className="header-title">
            <h1 data-testid="app-title">MapReduce Visual</h1>
            <p className="header-subtitle">Distributed Computing Dashboard</p>
          </div>
          <nav className="header-nav">
            <button
              data-testid="tab-dashboard"
              className={`nav-button ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveTab('dashboard')}
            >
              Dashboard
            </button>
            <button
              data-testid="tab-jobs"
              className={`nav-button ${activeTab === 'jobs' ? 'active' : ''}`}
              onClick={() => setActiveTab('jobs')}
            >
              Jobs
            </button>
            <button
              data-testid="tab-logs"
              className={`nav-button ${activeTab === 'logs' ? 'active' : ''}`}
              onClick={() => setActiveTab('logs')}
            >
              Logs
            </button>
          </nav>
        </div>
      </header>

      <main className="main-content">
        {activeTab === 'dashboard' && (
          <div className="dashboard-layout">
            <div className="dashboard-left">
              <JobForm onJobCreated={handleJobCreated} />
              {stats && <StatsPanel stats={stats} />}
            </div>
            <div className="dashboard-right">
              <EnginesDashboard engines={engines} />
            </div>
          </div>
        )}

        {activeTab === 'jobs' && (
          <div className="jobs-view">
            <JobsList jobs={jobs} />
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="logs-view">
            <LogsPanel logs={logs} />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
