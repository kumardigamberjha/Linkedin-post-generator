import { useState, useEffect } from 'react';
import './AdminPanel.css';

export default function AdminPanel({ onGenerateFromTrend, token }) {
  const [stats, setStats] = useState({ role: 'user', total_posts: 0, total_trends: 0, used_trends: 0, total_users: 0, active_subs: 0 });
  const [posts, setPosts] = useState([]);
  const [trends, setTrends] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTrend, setSelectedTrend] = useState(null);

  useEffect(() => {
    async function fetchData() {
      setIsLoading(true);
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      try {
        const [statsRes, postsRes, trendsRes] = await Promise.all([
          fetch('/api/admin/stats', { headers }),
          fetch('/api/admin/posts?limit=100', { headers }),
          fetch('/api/admin/trends?limit=100', { headers })
        ]);
        
        if (statsRes.ok) setStats(await statsRes.json());
        if (postsRes.ok) {
          const p = await postsRes.json();
          setPosts(p.items || []);
        }
        if (trendsRes.ok) {
          const t = await trendsRes.json();
          setTrends(t.items || []);
        }
      } catch (err) {
        console.error("Error fetching admin data", err);
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, [token]);

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}>
        <span className="spinner" style={{ width: 30, height: 30, borderWidth: 3 }} />
      </div>
    );
  }

  return (
    <div className="admin-panel">
      <div className="admin-header">
        <h1 className="admin-title">Admin Dashboard</h1>
      </div>

      <div className="admin-stats-grid">
        <div className="stat-card">
          <span className="stat-title">{stats.role === 'admin' ? 'Total Generated (All Users)' : 'Your Generated Posts'}</span>
          <span className="stat-value">{stats.total_posts}</span>
        </div>
        <div className="stat-card">
          <span className="stat-title">Trending Topics Tracked</span>
          <span className="stat-value">{stats.total_trends}</span>
        </div>
        <div className="stat-card">
          <span className="stat-title">Trends Used in Posts</span>
          <span className="stat-value">{stats.used_trends}</span>
        </div>
        {stats.role === 'admin' && (
          <>
            <div className="stat-card">
              <span className="stat-title">Total Registered Users</span>
              <span className="stat-value">{stats.total_users}</span>
            </div>
            <div className="stat-card">
              <span className="stat-title">Active Subscriptions</span>
              <span className="stat-value">{stats.active_subs}</span>
            </div>
          </>
        )}
      </div>

      <div className="admin-tables">
        <div className="admin-table-card">
          <div className="table-header">Generated Posts</div>
          <div className="table-container">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Topic</th>
                  <th>Niche</th>
                  <th>Provider</th>
                  <th>Words</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {posts.length === 0 ? (
                  <tr><td colSpan="6" style={{ textAlign: 'center' }}>No posts generated yet.</td></tr>
                ) : (
                  posts.map(post => (
                    <tr key={post.id}>
                      <td>#{post.id}</td>
                      <td><div className="text-truncate" title={post.topic}>{post.topic}</div></td>
                      <td>{post.niche}</td>
                      <td>{post.provider}</td>
                      <td>{post.word_count}</td>
                      <td>{new Date(post.created_at + 'Z').toLocaleString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="admin-table-card">
          <div className="table-header">Tracked Trending Topics</div>
          <div className="table-container">
            <table className="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Source</th>
                  <th>Topic</th>
                  <th>Niche</th>
                  <th>Status</th>
                  <th>Date Tracked</th>
                </tr>
              </thead>
              <tbody>
                {trends.length === 0 ? (
                  <tr><td colSpan="6" style={{ textAlign: 'center' }}>No trending topics tracked yet.</td></tr>
                ) : (
                  trends.map(trend => (
                    <tr key={trend.id} onClick={() => setSelectedTrend(trend)} style={{ cursor: 'pointer' }} title="Click to generate a post from this topic">
                      <td>#{trend.id}</td>
                      <td style={{ textTransform: 'capitalize' }}>{trend.source}</td>
                      <td><div className="text-truncate" title={trend.topic}>{trend.topic}</div></td>
                      <td>{trend.niche}</td>
                      <td>
                        <span className={`status-badge ${trend.used ? 'status-used' : 'status-unused'}`}>
                          {trend.used ? 'Used' : 'Not Used'}
                        </span>
                      </td>
                      <td>{new Date(trend.created_at + 'Z').toLocaleString()}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {selectedTrend && (
        <div className="history-modal-backdrop" onClick={() => setSelectedTrend(null)}>
          <div className="card" style={{ width: '100%', maxWidth: '420px', margin: 'auto', padding: '28px', cursor: 'default' }} onClick={e => e.stopPropagation()}>
            <h3 style={{ marginTop: 0, marginBottom: '16px', fontSize: '18px', color: 'var(--text)' }}>Generate Post?</h3>
            <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '24px', lineHeight: 1.5 }}>
              Do you want to start generating a LinkedIn post for this trending topic right now?
            </p>
            <div style={{ background: 'var(--bg-subtle)', padding: '14px', border: '1px solid var(--border)', borderRadius: '8px', fontSize: '14px', marginBottom: '24px', lineHeight: 1.5 }}>
              <div style={{ marginBottom: '6px' }}><strong style={{ color: 'var(--text)' }}>Topic:</strong> {selectedTrend.topic}</div>
              <div><strong style={{ color: 'var(--text)' }}>Niche:</strong> {selectedTrend.niche}</div>
            </div>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button className="btn btn-ghost" onClick={() => setSelectedTrend(null)}>Cancel</button>
              <button className="btn btn-primary" style={{ margin: 0, width: 'auto' }} onClick={() => {
                onGenerateFromTrend(selectedTrend.topic, selectedTrend.niche);
                setSelectedTrend(null);
              }}>
                Yes, Generate Post
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
