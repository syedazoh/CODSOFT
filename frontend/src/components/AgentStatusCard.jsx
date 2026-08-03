const HIDDEN_KEYS = new Set(['agent_id', 'agent_name'])

function formatLabel(key) {
  return key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function formatValue(value) {
  if (typeof value === 'number') {
    return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2)
  }
  return String(value)
}

function AgentStatusCard({ agentKey, status }) {
  if (!status) return null
  const fields = Object.entries(status).filter(([key]) => !HIDDEN_KEYS.has(key))

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-900">{status.agent_name || agentKey}</h3>
        <span className="text-xs text-gray-400 uppercase">{agentKey}</span>
      </div>
      <dl className="space-y-1">
        {fields.map(([key, value]) => (
          <div key={key} className="flex items-center justify-between text-sm">
            <dt className="text-gray-500">{formatLabel(key)}</dt>
            <dd className="text-gray-900 font-medium">{formatValue(value)}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

export default AgentStatusCard
