const AGENTS = [
  { key: 'hook',     label: 'Hook Finder',  match: 'Hook Finder' },
  { key: 'body',     label: 'Body Writer',  match: 'Body Writer' },
  { key: 'cta',      label: 'CTA Writer',   match: 'CTA Writer'  },
  { key: 'editor',   label: 'Editor',       match: 'Editor'      },
  { key: 'approver', label: 'Approver',     match: 'Approver'    },
]

function getAgentIndex(agentName) {
  return AGENTS.findIndex(a => agentName.includes(a.match))
}

export default function PipelineProgress({ steps, status }) {
  const lastAgentIndex = steps.length > 0
    ? getAgentIndex(steps[steps.length - 1].agent)
    : -1

  function getState(i) {
    if (status === 'done') return i <= lastAgentIndex ? 'done' : 'idle'
    if (i < lastAgentIndex) return 'done'
    if (i === lastAgentIndex && (status === 'running' || status === 'connecting')) return 'active'
    return 'idle'
  }

  const statusText =
    status === 'connecting' ? 'Connecting…' :
    status === 'running'    ? 'Running pipeline…' :
    status === 'done'       ? 'All steps complete' :
    status === 'error'      ? 'Pipeline failed' :
    'Waiting to start'

  const isLive = status === 'running' || status === 'connecting'

  return (
    <div className="pipeline-sidebar card">
      <div className="pipeline-sidebar-title">
        {isLive && <div className="spinner" style={{ width: 13, height: 13, borderWidth: 2 }} />}
        Pipeline
      </div>

      <div className="v-steps">
        {AGENTS.map((agent, i) => {
          const state = getState(i)
          return (
            <div key={agent.key} className="v-step-wrapper">
              <div className={`v-step ${state}`}>
                <div className="v-step-dot">
                  {state === 'done'
                    ? '✓'
                    : state === 'active'
                    ? <div className="spinner" style={{ width: 10, height: 10, borderWidth: 2 }} />
                    : i + 1}
                </div>
                <span className="v-step-label">{agent.label}</span>
              </div>
              {i < AGENTS.length - 1 && (
                <div className={`v-connector ${
                  state === 'done' || (i < lastAgentIndex) ? 'active' : ''
                }`} />
              )}
            </div>
          )
        })}
      </div>

      <p className="pipeline-status-text">{statusText}</p>
    </div>
  )
}
