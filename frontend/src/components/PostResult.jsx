import { useState, useEffect, useCallback } from 'react'

const ANGLE_LABELS = {
  'story':          'Story',
  'contrarian':     'Contrarian',
  'how-to':         'How-To',
  'lesson-learned': 'Lesson Learned',
}

export default function PostResult({ result, onReset, linkedinToken, linkedinUserId, onLinkedInConnect }) {
  const [copied, setCopied] = useState(false)
  const [posting, setPosting] = useState(false)
  const [posted, setPosted] = useState(false)
  const [postError, setPostError] = useState('')

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(result.post_text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {}
  }

  const doPost = useCallback(async (token, urn) => {
    setPosting(true)
    setPostError('')
    try {
      const resp = await fetch('/api/linkedin/post', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          post_text: result.post_text,
          access_token: token,
          author_urn: urn,
        }),
      })
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}))
        throw new Error(data.detail || `HTTP ${resp.status}`)
      }
      setPosted(true)
    } catch (e) {
      setPostError(e.message)
    } finally {
      setPosting(false)
    }
  }, [result])

  // Listen for postMessage from the OAuth popup
  useEffect(() => {
    function onMessage(e) {
      // Accept messages from the backend callback page
      if (e.origin !== 'http://localhost:8000' && e.origin !== window.location.origin) return
      if (!e.data || typeof e.data !== 'object') return

      if (e.data.type === 'li_auth') {
        const { token, uid } = e.data
        onLinkedInConnect(token, uid)
        doPost(token, `urn:li:person:${uid}`)
      } else if (e.data.type === 'li_error') {
        setPostError(`LinkedIn connection failed: ${e.data.error ?? 'unknown error'}`)
        setPosting(false)
      }
    }
    window.addEventListener('message', onMessage)
    return () => window.removeEventListener('message', onMessage)
  }, [doPost, onLinkedInConnect])

  function handlePostToLinkedIn() {
    if (linkedinToken && linkedinUserId) {
      // Already authenticated — post directly
      doPost(linkedinToken, `urn:li:person:${linkedinUserId}`)
    } else {
      // Open OAuth popup
      setPosting(true)
      setPostError('')
      const popup = window.open(
        '/api/linkedin/auth',
        'li-auth',
        'width=600,height=700,scrollbars=yes,resizable=yes'
      )
      if (!popup) {
        setPosting(false)
        setPostError('Popup was blocked. Allow popups for this site and try again.')
      }
    }
  }

  const approved = result.approved
  const angleLabel = ANGLE_LABELS[result.angle_type] || result.angle_type

  return (
    <div className="card">
      <div className="result-actions">
        <h2>Generated Post</h2>
        <button className="btn btn-ghost" onClick={onReset}>← New post</button>
      </div>

      <div className="stats-row">
        <span className="badge badge-blue">{angleLabel}</span>
        <span className="badge badge-grey">📝 {result.word_count} words</span>
        <span className="badge badge-grey"># {result.hashtag_count} hashtags</span>
        <span className="badge badge-grey">🔄 {result.cycles_taken} edit cycle{result.cycles_taken !== 1 ? 's' : ''}</span>
        {approved
          ? <span className="badge badge-green">✓ Approved</span>
          : <span className="badge badge-red">✗ Not approved</span>
        }
      </div>

      {!approved && result.approval_reasons?.length > 0 && (
        <div className="approval-reasons">
          <h4>Improvement notes</h4>
          <ul>
            {result.approval_reasons.map((r, i) => <li key={i}>{r}</li>)}
          </ul>
        </div>
      )}

      <div className="post-box">{result.post_text}</div>

      <div className="copy-btn-wrap">
        <button className="btn btn-secondary" onClick={handleCopy}>
          {copied ? '✓ Copied!' : 'Copy to clipboard'}
        </button>

        {posted ? (
          <span className="badge badge-green" style={{ alignSelf: 'center' }}>✓ Posted to LinkedIn</span>
        ) : (
          <button className="btn btn-linkedin" onClick={handlePostToLinkedIn} disabled={posting}>
            {posting
              ? <><span className="spinner" style={{ width: 14, height: 14, borderWidth: 2 }} /> Posting…</>
              : linkedinToken ? 'Post to LinkedIn' : 'Connect & Post to LinkedIn'
            }
          </button>
        )}
      </div>

      {postError && (
        <p style={{ color: 'var(--error)', fontSize: '0.85rem', marginTop: '0.5rem' }}>
          {postError}
        </p>
      )}

      <div className="result-footer">
        <button className="btn btn-primary" style={{ width: 'auto' }} onClick={onReset}>
          Generate another post
        </button>
      </div>
    </div>
  )
}
