import { useState, useRef, useEffect, useCallback } from 'react'
import GenerateForm from './components/GenerateForm'
import PipelineProgress from './components/PipelineProgress'
import AgentOutputFeed from './components/AgentOutputFeed'
import PostResult from './components/PostResult'
import HistoryPanel from './components/HistoryPanel'
import HistoryModal from './components/HistoryModal'
import AdminPanel from './components/AdminPanel'
import AuthForms from './components/AuthForms'
import Pricing from './components/Pricing'
import './App.css'

const WS_URL = 'ws://localhost:8000/api/ws/generate'

export default function App() {
  const [form, setForm] = useState({ topic: '', niche: 'ai', provider: 'google' })
  const [status, setStatus] = useState('idle')
  const [steps, setSteps] = useState([])
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [linkedinToken, setLinkedinToken] = useState('')
  const [linkedinUserId, setLinkedinUserId] = useState('')
  const [generatingTopic, setGeneratingTopic] = useState('')
  const [isFetchingTrends, setIsFetchingTrends] = useState(false)
  const [historyItems, setHistoryItems] = useState([])
  const [showHistory, setShowHistory] = useState(false)
  const [currentView, setCurrentView] = useState('generator') // 'generator', 'admin', 'login', 'signup', 'pricing'
  const [token, setToken] = useState(() => localStorage.getItem('auth_token') || '')
  const [currentUser, setCurrentUser] = useState(null)
  const [theme, setTheme] = useState(() =>
    localStorage.getItem('theme') ||
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
  )
  const wsRef = useRef(null)

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  const fetchHistory = useCallback(async () => {
    try {
      const r = await fetch('/api/history?limit=3')
      const data = await r.json()
      setHistoryItems(data.items ?? [])
    } catch {}
  }, [])

  useEffect(() => { fetchHistory() }, [fetchHistory])

  useEffect(() => {
    if (token) {
      fetch('/api/auth/me', { headers: { 'Authorization': `Bearer ${token}` } })
        .then(res => res.ok ? res.json() : null)
        .then(data => {
          if (data) setCurrentUser(data);
          else handleLogout();
        })
        .catch(() => handleLogout());
    }
  }, [token]);

  const handleLogout = () => {
    setToken('');
    setCurrentUser(null);
    localStorage.removeItem('auth_token');
    setCurrentView('login');
  };

  const toggleTheme = useCallback(() => {
    setTheme(t => t === 'light' ? 'dark' : 'light')
  }, [])


  function handleGenerate(overrideTopic, overrideNiche) {
    const finalTopic = typeof overrideTopic === 'string' ? overrideTopic : form.topic;
    const finalNiche = typeof overrideNiche === 'string' ? overrideNiche : form.niche;

    if (!finalTopic.trim()) return
    setGeneratingTopic(finalTopic.trim())
    setStatus('connecting')
    setSteps([])
    setResult(null)
    setError('')

    const ws = new WebSocket(WS_URL)
    wsRef.current = ws

    ws.onopen = () => {
      setStatus('running')
      ws.send(JSON.stringify({ topic: finalTopic, niche: finalNiche, provider: form.provider, token: token }))
    }

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.type === 'step') {
        setSteps(prev => [...prev, { agent: msg.agent, task: msg.task, output: msg.output }])
      } else if (msg.type === 'done') {
        setResult(msg.result)
        setStatus('done')
        fetchHistory()
      } else if (msg.type === 'error') {
        setError(msg.message)
        setStatus('error')
      }
    }

    ws.onerror = () => {
      setError('WebSocket connection failed. Make sure the backend is running on port 8000.')
      setStatus('error')
    }
  }

  function handleReset() {
    setStatus('idle')
    setSteps([])
    setResult(null)
    setError('')
  }

  const isRunning = status === 'connecting' || status === 'running'

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-inner">
          <div className="header-left">
            <div className="logo">
              <svg viewBox="0 0 24 24" fill="currentColor" className="logo-icon">
                <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
              </svg>
              <span>Post Generator</span>
            </div>
            <p className="header-subtitle">7-phase AI pipeline · Hook → Body → CTA → QA → Approve</p>
          </div>

          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <button
              className={`btn btn-ghost ${currentView === 'generator' ? 'active' : ''}`}
              onClick={() => setCurrentView('generator')}
              style={currentView === 'generator' ? { background: 'var(--surface)', color: 'var(--linkedin-blue)' } : {}}
            >
              Generator
            </button>
            <button
              className={`btn btn-ghost ${currentView === 'pricing' ? 'active' : ''}`}
              onClick={() => setCurrentView('pricing')}
              style={currentView === 'pricing' ? { background: 'var(--surface)', color: 'var(--linkedin-blue)' } : {}}
            >
              Pricing
            </button>
            {token && (
              <button
                className={`btn btn-ghost ${currentView === 'admin' ? 'active' : ''}`}
                onClick={() => setCurrentView('admin')}
                style={currentView === 'admin' ? { background: 'var(--surface)', color: 'var(--linkedin-blue)' } : {}}
              >
                Admin
              </button>
            )}
            {token ? (
              <button className="btn btn-ghost" onClick={handleLogout} style={{ color: 'var(--danger)' }}>Logout</button>
            ) : (
              <button className="btn btn-primary" onClick={() => setCurrentView('login')} style={{ padding: '6px 12px', margin: 0 }}>Log In</button>
            )}
            
            <button
              className="theme-toggle"
              onClick={toggleTheme}
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
            {theme === 'dark' ? (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="5"/>
                <line x1="12" y1="1" x2="12" y2="3"/>
                <line x1="12" y1="21" x2="12" y2="23"/>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                <line x1="1" y1="12" x2="3" y2="12"/>
                <line x1="21" y1="12" x2="23" y2="12"/>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
              </svg>
            )}
          </button>
          </div>
        </div>
      </header>

      {currentView === 'login' || currentView === 'signup' ? (
        <main className="app-main" style={{ display: 'block' }}>
          <AuthForms 
            view={currentView} 
            setView={setCurrentView} 
            onAuthSuccess={(t) => {
              setToken(t);
              setCurrentView('generator');
            }} 
          />
        </main>
      ) : currentView === 'pricing' ? (
        <main className="app-main" style={{ display: 'block' }}>
          <Pricing token={token} />
        </main>
      ) : currentView === 'admin' ? (
        <main className="app-main" style={{ display: 'block' }}>
          <AdminPanel 
            token={token}
            onGenerateFromTrend={(t, n) => {
              setForm(f => ({ ...f, topic: t, niche: n }));
              setCurrentView('generator');
              handleGenerate(t, n);
            }} 
          />
        </main>
      ) : (
        <main className="app-main">
          <div className="left-panel">
            {status !== 'done' && (
              <GenerateForm
                form={form}
                setForm={setForm}
                onGenerate={handleGenerate}
                disabled={isRunning}
                error={status === 'error' ? error : ''}
                isFetchingTrends={isFetchingTrends}
                setIsFetchingTrends={setIsFetchingTrends}
                token={token}
              />
            )}

            {steps.length > 0 && <AgentOutputFeed steps={steps} />}

            {status === 'done' && result && (
              <PostResult
                result={result}
                onReset={handleReset}
                linkedinToken={linkedinToken}
                linkedinUserId={linkedinUserId}
                onLinkedInConnect={(token, uid) => {
                  setLinkedinToken(token)
                  setLinkedinUserId(uid)
                }}
              />
            )}
          </div>

          <div className="right-panel">
            {generatingTopic && (
              <div className="current-topic-card card">
                <span className="current-topic-label">
                  {isRunning ? 'Generating…' : 'Last generated'}
                </span>
                <p className="current-topic-text">"{generatingTopic}"</p>
                {isRunning && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 6 }}>
                    <span className="spinner" style={{ width: 12, height: 12, borderWidth: 2 }} />
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Pipeline running</span>
                  </div>
                )}
              </div>
            )}
            {isFetchingTrends && (
              <div className="current-topic-card card" style={{ marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} />
                  <span style={{ fontSize: '13px', fontWeight: 500, color: 'var(--text)' }}>
                    Searching for trending topics...
                  </span>
                </div>
              </div>
            )}
            <PipelineProgress steps={steps} status={status} />
            <HistoryPanel
              items={historyItems}
              onViewAll={() => setShowHistory(true)}
              onSelect={item => {
                setResult({
                  post_text: item.post_text,
                  angle_type: item.angle_type,
                  word_count: item.word_count,
                  approved: !!item.approved,
                  approval_reasons: [],
                  hashtag_count: 0,
                  cycles_taken: 0,
                })
                setGeneratingTopic(item.topic)
                setStatus('done')
              }}
            />
          </div>
        </main>
      )}

      {showHistory && (
        <HistoryModal
          onClose={() => setShowHistory(false)}
          onSelect={item => {
            setResult({
              post_text: item.post_text,
              angle_type: item.angle_type,
              word_count: item.word_count,
              approved: !!item.approved,
              approval_reasons: [],
              hashtag_count: 0,
              cycles_taken: 0,
            })
            setGeneratingTopic(item.topic)
            setStatus('done')
            setShowHistory(false)
          }}
        />
      )}
    </div>
  )
}
