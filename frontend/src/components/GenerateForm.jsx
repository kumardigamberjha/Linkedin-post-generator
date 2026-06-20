const PROVIDER_GROUPS = [
  {
    label: 'Cloud API',
    options: [
      { value: 'google/gemini-3.5-flash', label: 'Google – Gemini 3.5 Flash' },
      { value: 'nvidia/z-ai/glm-5.1', label: 'NVIDIA – GLM 5.1' },
    ],
  },
  {
    label: 'Ollama Cloud',
    options: [
      { value: 'ollama/gemma4:31b-cloud', label: 'Ollama – Gemma4 31B' },
    ],
  },
]

import { useState } from 'react'

export default function GenerateForm({ form, setForm, onGenerate, disabled, error, isFetchingTrends, setIsFetchingTrends, token }) {
  const [trends, setTrends] = useState(null)

  async function fetchTrends() {
    if (!form.niche.trim()) {
      alert("Please enter a niche first.");
      return;
    }
    if (!token) {
      alert("Please log in to search for trending topics.");
      return;
    }
    setIsFetchingTrends(true);
    setTrends(null);
    try {
      const res = await fetch(`http://localhost:8000/api/trends?niche=${encodeURIComponent(form.niche)}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (!res.ok) throw new Error("Failed to fetch trends");
      const data = await res.json();
      setTrends(data);
    } catch (err) {
      console.error(err);
      alert("Error fetching trends");
    } finally {
      setIsFetchingTrends(false);
    }
  }

  function handleTrendClick(trendText) {
    setForm(f => ({ ...f, topic: trendText }));
  }

  function handleSubmit(e) {
    e.preventDefault()
    onGenerate()
  }

  return (
    <div className="card">
      <h1 className="card-title">Generate a LinkedIn Post</h1>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="topic">Topic *</label>
          <textarea
            id="topic"
            value={form.topic}
            onChange={e => setForm(f => ({ ...f, topic: e.target.value }))}
            placeholder="What do you want to post about? e.g. 'How I went from 0 to 10k followers using AI content'"
            disabled={disabled}
            required
          />
        </div>

        <div className="form-row">
          <div className="form-group" style={{ flex: 1 }}>
            <label htmlFor="niche">Niche</label>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
              <div style={{ flex: 1 }}>
                <input
                  id="niche"
                  type="text"
                  value={form.niche}
                  onChange={e => setForm(f => ({ ...f, niche: e.target.value }))}
                  placeholder="ai, saas, marketing…"
                  disabled={disabled}
                  style={{ width: '100%' }}
                />
                <span className="form-hint">The industry / audience context</span>
              </div>
              {token ? (
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  onClick={fetchTrends}
                  disabled={isFetchingTrends || disabled}
                  style={{ padding: '0.6rem 1rem', whiteSpace: 'nowrap' }}
                >
                  {isFetchingTrends ? 'Finding...' : 'Find Trends'}
                </button>
              ) : (
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  disabled
                  style={{ padding: '0.6rem 1rem', whiteSpace: 'nowrap', opacity: 0.6, cursor: 'not-allowed' }}
                  title="Log in to find trends"
                >
                  Find Trends
                </button>
              )}
            </div>
            
            {trends && (
              <div className="trends-container">
                {Object.entries(trends).map(([source, topics]) => (
                  topics && topics.length > 0 && (
                    <div key={source} className="trend-source-group">
                      <div className="trend-source-title">
                        {source === 'serpapi' ? 'Google' : 
                         source === 'duckduckgo' ? 'DuckDuckGo' : 
                         source === 'hackernews' ? 'Hacker News' : 'Quora'}
                      </div>
                      <div className="trend-chips">
                        {topics.map((t, idx) => (
                          <button
                            key={idx}
                            type="button"
                            className="trend-chip"
                            onClick={() => handleTrendClick(t)}
                            title="Click to use this topic"
                          >
                            {t}
                          </button>
                        ))}
                      </div>
                    </div>
                  )
                ))}
              </div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="provider">Model</label>
            <select
              id="provider"
              value={form.provider}
              onChange={e => setForm(f => ({ ...f, provider: e.target.value }))}
              disabled={disabled}
            >
              {PROVIDER_GROUPS.map(group => (
                <optgroup key={group.label} label={group.label}>
                  {group.options.map(p => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>
        </div>

        {error && (
          <div className="error-banner">
            <span>⚠</span>
            <span>{error}</span>
          </div>
        )}

        <button className="btn btn-primary" type="submit" disabled={disabled || !form.topic.trim()}>
          {disabled ? (
            <>
              <span className="spinner" style={{ width: 16, height: 16, borderWidth: 2 }} />
              Generating…
            </>
          ) : 'Generate Post'}
        </button>
      </form>
    </div>
  )
}
