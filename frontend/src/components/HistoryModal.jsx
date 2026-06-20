import { useState, useEffect, useCallback } from 'react'

const ANGLE_LABELS = {
  story: 'Story',
  contrarian: 'Contrarian',
  'how-to': 'How-To',
  'lesson-learned': 'Lesson',
}

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr + 'Z').getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${Math.max(1, mins)}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days < 7) return `${days}d ago`
  return new Date(dateStr).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export default function HistoryModal({ onClose, onSelect }) {
  const [items, setItems] = useState([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(false)
  const PAGE = 20

  const fetchPage = useCallback(async (off) => {
    setLoading(true)
    try {
      const r = await fetch(`/api/history?limit=${PAGE}&offset=${off}`)
      const data = await r.json()
      setItems(prev => off === 0 ? data.items : [...prev, ...data.items])
      setTotal(data.total)
      setOffset(off + data.items.length)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { fetchPage(0) }, [fetchPage])

  // Close on Escape
  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  return (
    <div className="history-modal-backdrop" onClick={onClose}>
      <div className="history-modal card" onClick={e => e.stopPropagation()}>
        <div className="history-modal-header">
          <h2 className="history-modal-title">Post History</h2>
          <button className="btn btn-ghost" onClick={onClose} aria-label="Close">✕</button>
        </div>

        {items.length === 0 && !loading ? (
          <p className="history-empty" style={{ padding: '24px 0' }}>No posts generated yet.</p>
        ) : (
          <ul className="history-modal-list">
            {items.map(item => (
              <li key={item.id} className="history-modal-row" onClick={() => onSelect(item)}>
                <div className="history-modal-row-main">
                  <p className="history-modal-topic">{item.topic}</p>
                  <div className="history-modal-meta">
                    {item.angle_type && (
                      <span className="badge badge-blue">{ANGLE_LABELS[item.angle_type] ?? item.angle_type}</span>
                    )}
                    <span className="badge badge-grey">{item.word_count}w</span>
                    {item.approved
                      ? <span className="badge badge-green">✓ Approved</span>
                      : <span className="badge badge-red">✗ Not approved</span>
                    }
                  </div>
                </div>
                <span className="history-modal-time">{timeAgo(item.created_at)}</span>
              </li>
            ))}
          </ul>
        )}

        {offset < total && (
          <div style={{ textAlign: 'center', marginTop: 16 }}>
            <button className="btn btn-ghost" onClick={() => fetchPage(offset)} disabled={loading}>
              {loading ? 'Loading…' : `Load more (${total - offset} remaining)`}
            </button>
          </div>
        )}

        {loading && items.length === 0 && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '24px 0' }}>
            <span className="spinner" />
          </div>
        )}
      </div>
    </div>
  )
}
