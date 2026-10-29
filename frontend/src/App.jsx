import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Upload, Play, Pause, Square, LogIn, LogOut, 
  RefreshCw, CheckCircle, XCircle, Clock, Search
} from 'lucide-react';
import { format } from 'date-fns';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [authStatus, setAuthStatus] = useState({ authenticated: false, email: '' });
  const [stats, setStats] = useState({ total: 0, not_sent: 0, scheduled: 0, draft_created: 0, failed: 0 });
  const [contacts, setContacts] = useState([]);
  const [logs, setLogs] = useState([]);
  const [scheduleStatus, setScheduleStatus] = useState(null);
  
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [activeTab, setActiveTab] = useState('contacts');
  
  const [config, setConfig] = useState({
    start_date: format(new Date(), 'yyyy-MM-dd'),
    start_time: '10:00',
    interval_minutes: 10,
    daily_limit: 20
  });

  const [previewContact, setPreviewContact] = useState(null);

  // Initialize
  useEffect(() => {
    checkAuth();
    fetchStats();
    fetchContacts();
    fetchLogs();
    fetchScheduleStatus();
    
    // Poll for updates every 5 seconds if active
    const interval = setInterval(() => {
      fetchStats();
      fetchContacts();
      fetchLogs();
      fetchScheduleStatus();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const checkAuth = async () => {
    try {
      const res = await axios.get(`${API_BASE}/gmail/status`);
      setAuthStatus(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleLogin = async () => {
    try {
      const res = await axios.get(`${API_BASE}/gmail/auth-url`);
      window.location.href = res.data.url;
    } catch (e) {
      alert("Failed to get auth URL");
    }
  };

  const handleDisconnect = async () => {
    try {
      await axios.post(`${API_BASE}/gmail/disconnect`);
      checkAuth();
    } catch (e) {
      console.error(e);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files[0]) setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    try {
      await axios.post(`${API_BASE}/contacts/upload`, formData);
      alert('Upload successful');
      setFile(null);
      fetchStats();
      fetchContacts();
    } catch (e) {
      alert(`Upload failed: ${e.response?.data?.detail || e.message}`);
    } finally {
      setUploading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API_BASE}/contacts/stats`);
      setStats(res.data);
    } catch (e) { }
  };

  const fetchContacts = async () => {
    try {
      const res = await axios.get(`${API_BASE}/contacts/`);
      setContacts(res.data);
    } catch (e) { }
  };

  const fetchLogs = async () => {
    try {
      const res = await axios.get(`${API_BASE}/logs/`);
      setLogs(res.data);
    } catch (e) { }
  };

  const fetchScheduleStatus = async () => {
    try {
      const res = await axios.get(`${API_BASE}/schedule/status`);
      setScheduleStatus(res.data);
    } catch (e) { }
  };

  const handleSaveConfig = async () => {
    try {
      await axios.post(`${API_BASE}/schedule/config`, config);
      alert('Configuration saved');
    } catch (e) {
      alert('Failed to save configuration');
    }
  };

  const handleStart = async (mode = 'live') => {
    if (!authStatus.authenticated && mode === 'live') {
      alert('Please connect Gmail first for live mode.');
      return;
    }
    
    // We need a batch ID to start. For MVP, we'll just get the latest batch
    try {
      const batchesRes = await axios.get(`${API_BASE}/contacts/batches`);
      if (batchesRes.data.length === 0) {
        alert('No contacts uploaded yet.');
        return;
      }
      const latestBatch = batchesRes.data[batchesRes.data.length - 1].batch_id;
      
      await handleSaveConfig(); // ensure saved
      
      await axios.post(`${API_BASE}/schedule/start?batch_id=${latestBatch}&mode=${mode}`);
      fetchScheduleStatus();
      fetchStats();
    } catch (e) {
      alert(`Failed to start: ${e.response?.data?.detail || e.message}`);
    }
  };

  const handleAction = async (action) => {
    try {
      await axios.post(`${API_BASE}/schedule/${action}`);
      fetchScheduleStatus();
    } catch (e) {
      alert(`Action failed`);
    }
  };

  const handlePreview = async (id) => {
    try {
      const res = await axios.get(`${API_BASE}/contacts/${id}/preview`);
      setPreviewContact(res.data);
    } catch (e) {
      alert('Preview failed');
    }
  };

  return (
    <div className="container">
      <header className="header">
        <h1>DraftMaster AI</h1>
        <div className={`auth-status ${authStatus.authenticated ? 'authenticated' : 'unauthenticated'}`}>
          {authStatus.authenticated ? (
            <>
              <CheckCircle size={16} /> Connected: {authStatus.email}
              <button className="auth-btn disconnect" onClick={handleDisconnect} style={{marginLeft: '10px', padding: '0.2rem 0.5rem', fontSize:'0.8rem'}}>Disconnect</button>
            </>
          ) : (
            <>
              <XCircle size={16} /> Gmail Not Connected
              <button className="auth-btn" onClick={handleLogin} style={{marginLeft: '10px', display:'flex', alignItems:'center', gap:'0.2rem'}}><LogIn size={14}/> Connect Gmail</button>
            </>
          )}
        </div>
      </header>

      <div className="grid">
        {/* Left Column: Upload & Stats */}
        <div>
          <div className="panel" style={{marginBottom: '1.5rem'}}>
            <h2><Upload size={20} /> Import Contacts</h2>
            <div className="upload-area" onClick={() => document.getElementById('file-upload').click()}>
              <input 
                id="file-upload" 
                type="file" 
                accept=".xlsx,.csv" 
                style={{display: 'none'}} 
                onChange={handleFileChange} 
              />
              {file ? (
                <div>
                  <p style={{color: 'var(--accent)', fontWeight: 'bold'}}>{file.name}</p>
                  <p style={{fontSize: '0.8rem', color: 'var(--text-muted)'}}>{(file.size / 1024).toFixed(1)} KB</p>
                </div>
              ) : (
                <p style={{color: 'var(--text-muted)'}}>Click to select .xlsx or .csv</p>
              )}
            </div>
            {file && (
              <button 
                className="btn btn-primary" 
                style={{width: '100%', marginTop: '1rem', justifyContent: 'center'}}
                onClick={handleUpload}
                disabled={uploading}
              >
                {uploading ? 'Uploading...' : 'Upload Data'}
              </button>
            )}
          </div>

          <div className="panel">
            <h2><CheckCircle size={20} /> Current Status</h2>
            <div className="stats-grid">
              <div className="stat-card">
                <div className="value">{stats.total}</div>
                <div className="label">Total</div>
              </div>
              <div className="stat-card">
                <div className="value" style={{color: 'var(--text-main)'}}>{stats.not_sent}</div>
                <div className="label">Ready</div>
              </div>
              <div className="stat-card">
                <div className="value" style={{color: '#60a5fa'}}>{stats.scheduled}</div>
                <div className="label">Scheduled</div>
              </div>
              <div className="stat-card">
                <div className="value" style={{color: 'var(--success)'}}>{stats.draft_created}</div>
                <div className="label">Drafts Created</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Schedule & Controls */}
        <div>
          <div className="panel" style={{marginBottom: '1.5rem'}}>
            <h2><Clock size={20} /> Schedule Configuration</h2>
            <div className="grid" style={{gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: 0}}>
              <div className="form-group">
                <label>Start Date</label>
                <input 
                  type="date" 
                  className="form-control" 
                  value={config.start_date}
                  onChange={e => setConfig({...config, start_date: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Start Time</label>
                <input 
                  type="time" 
                  className="form-control" 
                  value={config.start_time}
                  onChange={e => setConfig({...config, start_time: e.target.value})}
                />
              </div>
              <div className="form-group">
                <label>Interval (minutes)</label>
                <input 
                  type="number" 
                  className="form-control" 
                  value={config.interval_minutes}
                  onChange={e => setConfig({...config, interval_minutes: parseInt(e.target.value) || 0})}
                />
              </div>
              <div className="form-group">
                <label>Daily Limit</label>
                <input 
                  type="number" 
                  className="form-control" 
                  value={config.daily_limit}
                  onChange={e => setConfig({...config, daily_limit: parseInt(e.target.value) || 0})}
                />
              </div>
            </div>
          </div>

          <div className="panel">
            <h2><Play size={20} /> Controls</h2>
            
            {scheduleStatus?.is_active ? (
              <div>
                <p style={{color: 'var(--text-muted)', marginBottom: '1rem'}}>
                  Scheduler is <strong>{scheduleStatus.is_paused ? 'PAUSED' : 'RUNNING'}</strong> 
                  <span className="badge" style={{marginLeft:'0.5rem', background:'rgba(255,255,255,0.1)'}}>{scheduleStatus.mode.toUpperCase()} MODE</span>
                </p>
                <div className="controls">
                  {scheduleStatus.is_paused ? (
                    <button className="btn btn-success" onClick={() => handleAction('resume')}><Play size={16}/> Resume</button>
                  ) : (
                    <button className="btn btn-warning" onClick={() => handleAction('pause')}><Pause size={16}/> Pause</button>
                  )}
                  <button className="btn btn-danger" onClick={() => handleAction('stop')}><Square size={16}/> Stop</button>
                </div>
              </div>
            ) : (
              <div>
                <p style={{color: 'var(--text-muted)', marginBottom: '1rem'}}>Scheduler is stopped.</p>
                <div className="controls">
                  <button className="btn btn-primary" onClick={() => handleStart('live')}><Play size={16}/> Start Live</button>
                  <button className="btn btn-outline" onClick={() => handleStart('preview')}><Search size={16}/> Dry Run (Preview)</button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="panel" style={{flex: 1, display: 'flex', flexDirection: 'column'}}>
        <div className="tabs">
          <div className={`tab ${activeTab === 'contacts' ? 'active' : ''}`} onClick={() => setActiveTab('contacts')}>
            Contacts List
          </div>
          <div className={`tab ${activeTab === 'logs' ? 'active' : ''}`} onClick={() => setActiveTab('logs')}>
            Activity Logs
          </div>
        </div>

        {activeTab === 'contacts' && (
          <div className="table-container" style={{flex: 1}}>
            <table>
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Company</th>
                  <th>Contact</th>
                  <th>Email</th>
                  <th>Status</th>
                  <th>Scheduled For</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {contacts.length === 0 ? (
                  <tr><td colSpan="7" style={{textAlign:'center', color:'var(--text-muted)'}}>No contacts found.</td></tr>
                ) : contacts.map(c => (
                  <tr key={c.id}>
                    <td>{c.row_index}</td>
                    <td>{c.company}</td>
                    <td>{c.contact_name}</td>
                    <td>{c.email}</td>
                    <td><span className={`badge status-${c.status}`}>{c.status.replace('_', ' ')}</span></td>
                    <td style={{color: 'var(--text-muted)'}}>
                      {c.scheduled_time ? format(new Date(c.scheduled_time), 'dd MMM, HH:mm') : '—'}
                    </td>
                    <td>
                      <button className="btn btn-outline" style={{padding:'0.25rem 0.5rem', fontSize:'0.75rem'}} onClick={() => handlePreview(c.id)}>Preview</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {activeTab === 'logs' && (
          <div className="table-container" style={{flex: 1}}>
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Target</th>
                  <th>Status</th>
                  <th>Message / Error</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 ? (
                  <tr><td colSpan="4" style={{textAlign:'center', color:'var(--text-muted)'}}>No activity yet.</td></tr>
                ) : logs.map(l => (
                  <tr key={l.id}>
                    <td style={{color: 'var(--text-muted)'}}>{format(new Date(l.created_at + 'Z'), 'dd MMM, HH:mm:ss')}</td>
                    <td>{l.company ? `${l.company} (${l.contact_name})` : '—'}</td>
                    <td><span className={`badge status-${l.status === 'Draft Created' ? 'DRAFT_CREATED' : l.status.toUpperCase()}`}>{l.status}</span></td>
                    <td style={{maxWidth: '300px', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap'}} title={l.error || l.message}>
                      {l.error ? <span style={{color:'var(--danger)'}}>{l.error}</span> : l.message}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Preview Modal */}
      {previewContact && (
        <div className="modal-overlay" onClick={() => setPreviewContact(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Draft Preview</h2>
              <button className="btn btn-outline" onClick={() => setPreviewContact(null)} style={{padding:'0.25rem 0.5rem'}}>Close</button>
            </div>
            <div className="modal-body">
              <div style={{marginBottom: '1rem'}}>
                <strong>To:</strong> {previewContact.contact_name} &lt;{previewContact.email}&gt;
              </div>
              <div style={{marginBottom: '1rem'}}>
                <strong>Subject:</strong> {previewContact.subject}
              </div>
              <div className="preview-email">
                {previewContact.body}
              </div>
              <div style={{marginTop: '1.5rem', padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', color: 'var(--danger)', borderRadius: '0.5rem', border: '1px solid rgba(239, 68, 68, 0.2)', display: 'flex', alignItems: 'center', gap: '0.5rem'}}>
                <XCircle size={20} />
                <span style={{fontSize: '0.875rem', fontWeight: 500}}>
                  This is a preview. The system will ONLY create a draft. It will NEVER send the email automatically.
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}

export default App;
