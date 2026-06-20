function extractOutput(agentName, rawOutput) {
  try {
    const obj = JSON.parse(rawOutput)
    if (agentName.includes('Hook Finder') && obj.selected_hook)
      return { type: 'text', value: obj.selected_hook }
    if (agentName.includes('Body Writer') && obj.body)
      return { type: 'text', value: obj.body }
    if (agentName.includes('CTA Writer') && obj.cta_text)
      return { type: 'text', value: obj.cta_text }
    if (agentName.includes('Editor') && obj.revised_post) {
      const v = obj.revised_post
      return { type: 'text', value: v.length > 300 ? v.slice(0, 300) + '…' : v }
    }
    if (agentName.includes('Approver'))
      return { type: 'approval', approved: obj.approved, reasons: obj.reasons || [] }
    const keys = Object.keys(obj)
    const first = obj[keys[0]]
    if (typeof first === 'string')
      return { type: 'text', value: first.length > 200 ? first.slice(0, 200) + '…' : first }
  } catch {}
  const s = String(rawOutput)
  return { type: 'text', value: s.length > 200 ? s.slice(0, 200) + '…' : s }
}

export default function AgentOutputFeed({ steps }) {
  return (
    <div className="agent-output-feed">
      {steps.map((step, i) => {
        const out = extractOutput(step.agent, step.output)
        return (
          <div key={i} className="agent-output-card">
            <div className="aoc-header">
              <span className="aoc-badge">{step.agent}</span>
              <span className="aoc-task">{step.task}</span>
            </div>
            {out.type === 'approval' ? (
              <div className="aoc-approval">
                <span className={`badge ${out.approved ? 'badge-green' : 'badge-red'}`}>
                  {out.approved ? '✓ Approved' : '✗ Not approved'}
                </span>
                {out.reasons.length > 0 && (
                  <ul className="aoc-reasons">
                    {out.reasons.map((r, j) => <li key={j}>{r}</li>)}
                  </ul>
                )}
              </div>
            ) : (
              <p className="aoc-text">{out.value}</p>
            )}
          </div>
        )
      })}
    </div>
  )
}
