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
  return `${Math.floor(days / 7)}w ago`
}

export default function HistoryPanel({ items, onViewAll, onSelect }) {
  return (
    <div className="history-panel card">
      <div className="history-panel-header">
        <span className="history-panel-title">Recent Posts</span>
        {items.length > 0 && (
          <button className="history-view-all-btn" onClick={onViewAll}>
            View all →
          </button>
        )}
      </div>

      {items.length === 0 ? (
        <p className="history-empty">No posts yet. Generate your first one.</p>
      ) : (
        <ul className="history-list">
          {items.map(item => (
            <li key={item.id} className="history-item" onClick={() => onSelect(item)}>
              <div className="history-item-top">
                {item.angle_type && (
                  <span className="badge badge-blue history-angle">
                    {ANGLE_LABELS[item.angle_type] ?? item.angle_type}
                  </span>
                )}
                <span className="history-time">{timeAgo(item.created_at)}</span>
              </div>
              <p className="history-topic">{item.topic}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
