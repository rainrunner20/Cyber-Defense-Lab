import { useState } from 'react';
import './App.css';

const API = (import.meta.env.VITE_API_URL || 'http://localhost:5000').replace(/\/+$/, '');
const TYPES = [
  { value: 'failed_login', label: 'Failed login attempts', detail: 'Demonstrates repeated invalid credentials', icon: '🔑' },
  { value: 'blocked_request', label: 'Blocked web request', detail: 'Simulates a policy-denied request', icon: '🛡️' },
  { value: 'suspicious_volume', label: 'Unexpected request volume', detail: 'Simulates an activity spike for triage', icon: '📈' },
];

async function request(path, options = {}, token = '') {
  const response = await fetch(API + path, {
    ...options,
    headers: {
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: 'Bearer ' + token } : {}),
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || 'The training API is unavailable.');
  }
  return data;
}

export default function App() {
  const [mode, setMode] = useState('register');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [team, setTeam] = useState('blue');
  const [session, setSession] = useState(null);
  const [events, setEvents] = useState([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  async function reload(accessToken) {
    const data = await request('/api/events', {}, accessToken);
    setEvents(data.events);
  }

  async function submit(event) {
    event.preventDefault();
    setBusy(true);
    setMessage('');
    try {
      if (mode === 'register') {
        await request('/register', {
          method: 'POST', body: JSON.stringify({ username, password, team }),
        });
        setMode('login');
        setMessage('Account created. Sign in to open your practice dashboard.');
      } else {
        const data = await request('/login', {
          method: 'POST', body: JSON.stringify({ username, password }),
        });
        await reload(data.access_token);
        setSession({ username: data.username, team: data.team, token: data.access_token });
        setPassword('');
        setMessage('Signed in. Your practice data is private to this account.');
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to finish request.');
    } finally {
      setBusy(false);
    }
  }

  async function createEvent(kind) {
    if (!session || busy) return;
    setBusy(true);
    setMessage('');
    try {
      await request('/api/events', { method: 'POST', body: JSON.stringify({ kind }) }, session.token);
      await reload(session.token);
      setMessage('One synthetic event added to your private training timeline.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Could not add the event.');
    } finally {
      setBusy(false);
    }
  }

  function signOut() {
    setSession(null);
    setEvents([]);
    setPassword('');
    setMessage('Signed out. The demo keeps access tokens in memory only.');
  }

  const high = events.filter(event => event.severity === 'high').length;
  const medium = events.filter(event => event.severity === 'medium').length;
  const low = events.filter(event => event.severity === 'low').length;

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand"><span className="mark">◈</span><strong>Cyber Defense Lab</strong></div>
        <span className="top-label">ISOLATED EDUCATIONAL SIMULATOR / v0.1</span>
        {session && <button className="text-button" onClick={signOut}>Sign out</button>}
      </header>

      <main>
        <div className="hero">
          <div className="eyebrow"><span className="signal" /> Blue-team fundamentals · synthetic activity</div>
          <h1>Investigate signals.<span> Not real attacks.</span></h1>
          <p>Explore a controlled security-event timeline, learn how incidents are triaged, and verify the behavior with automated tests. No live network traffic or external systems are targeted.</p>
        </div>

        {!session ? (
          <section className="auth card" aria-labelledby="auth-title">
            <div className="tabs">
              <button className={mode === 'register' ? 'selected' : ''} onClick={() => { setMode('register'); setMessage(''); }}>Create practice account</button>
              <button className={mode === 'login' ? 'selected' : ''} onClick={() => { setMode('login'); setMessage(''); }}>Sign in</button>
            </div>
            <h2 id="auth-title">{mode === 'register' ? 'Start a local training session' : 'Welcome back'}</h2>
            <p className="muted">The account exists only in your configured local training database.</p>
            <form onSubmit={submit} className="auth-fields">
              <label>Username
                <input required value={username} maxLength={50} autoComplete="username" onChange={e => setUsername(e.target.value)} placeholder="analyst_example" />
              </label>
              <label>Password
                <input required type="password" minLength={mode === 'register' ? 12 : 1} maxLength={128}
                  autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
                  value={password} onChange={e => setPassword(e.target.value)} placeholder="At least 12 characters" />
              </label>
              {mode === 'register' && <label>Learning perspective
                <select value={team} onChange={e => setTeam(e.target.value)}>
                  <option value="blue">Blue team — investigate</option>
                  <option value="red">Red team — understand test signals</option>
                </select>
                <span className="hint">This is a visual preference, not an administrator permission.</span>
              </label>}
              <button className="primary" disabled={busy} type="submit">{busy ? 'Working…' : mode === 'register' ? 'Create training account' : 'Open dashboard'}</button>
            </form>
          </section>
        ) : (
          <>
            <div className="session-bar">
              <div><span className="online-dot" /> <strong>{session.username}</strong> <span className="muted">· {session.team} perspective</span></div>
              <span className="tag">SYNTHETIC DATA ONLY</span>
            </div>
            <div className="metrics">
              <div className="card metric"><span>Total events</span><strong>{events.length}</strong><small>Your most recent 50 records</small></div>
              <div className="card metric"><span>High severity</span><strong>{high}</strong><small>Unusual simulated volume</small></div>
              <div className="card metric"><span>Medium / low</span><strong>{medium} / {low}</strong><small>Other activity patterns</small></div>
            </div>
            <section className="card activity">
              <div className="section-head"><div><h2>Generate a safe test signal</h2><p className="muted">Each action creates a record in this private demo account, not real security traffic.</p></div><span className="tag">TRAINING MODE</span></div>
              <div className="scenarios">
                {TYPES.map(item => <button className="scenario" disabled={busy} key={item.value} onClick={() => void createEvent(item.value)}>
                  <span className="emoji">{item.icon}</span><strong>{item.label}</strong><span>{item.detail}</span>
                  <span className="action">Add example event</span>
                </button>)}
              </div>
            </section>
            <section className="card timeline">
              <div className="section-head"><div><h2>Event timeline</h2><p className="muted">Limited to your most recent 50 local records.</p></div><span className="tag">{events.length} events</span></div>
              {events.length === 0 ? <p className="empty">No training events yet. Choose a scenario above to see the timeline populate.</p> :
                <div className="event-list">{events.map(item => <div className="event" key={item.id}>
                  <span className={'severity ' + item.severity}>{item.severity}</span>
                  <strong>{item.kind.replaceAll('_', ' ')}</strong>
                  <span className="muted">Synthetic</span>
                  <time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time>
                </div>)}</div>}
            </section>
          </>
        )}

        {message && <p className="message" role="status">{message}</p>}
        <footer>Security training exercise · No credential-harvesting, attack execution, network capture or claims of a production SIEM.</footer>
      </main>
    </div>
  );
}
