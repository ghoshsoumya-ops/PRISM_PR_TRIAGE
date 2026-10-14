import { AlertTriangle, ShieldCheck, ShieldAlert, ShieldX, Info, FileCode } from 'lucide-react'

const SEVERITY_CONFIG = {
  critical: { icon: ShieldX, color: '#f87171', bg: '#1c0f0f', border: '#5c1a1a' },
  high: { icon: ShieldAlert, color: '#fb923c', bg: '#1c150f', border: '#5c381a' },
  medium: { icon: AlertTriangle, color: '#facc15', bg: '#1c1a0f', border: '#5c4d1a' },
  low: { icon: ShieldCheck, color: '#4ade80', bg: '#0f1c15', border: '#1a5c32' },
}

function Finding({ finding }) {
  const config = SEVERITY_CONFIG[finding.severity] || SEVERITY_CONFIG.low
  const Icon = config.icon
  return (
    <div
      className="px-4 py-3 rounded-lg border"
      style={{ background: config.bg, borderColor: config.border }}
    >
      <div className="flex items-start gap-3">
        <Icon size={16} className="mt-0.5 shrink-0" style={{ color: config.color }} />
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium" style={{ color: config.color }}>
              {finding.title}
            </span>
            <span
              className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded font-medium"
              style={{ background: config.border, color: config.color }}
            >
              {finding.severity}
            </span>
            <span
              className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded"
              style={{ background: 'var(--navy-700)', color: 'var(--slate-400)' }}
            >
              {finding.category}
            </span>
          </div>
          <p className="text-sm mt-1" style={{ color: 'var(--slate-400)' }}>
            {finding.description}
          </p>
          {finding.file && (
            <div className="flex items-center gap-1.5 mt-1.5">
              <FileCode size={12} style={{ color: 'var(--slate-400)' }} />
              <code
                className="text-xs px-1.5 py-0.5 rounded"
                style={{ background: 'var(--navy-800)', color: 'var(--slate-400)' }}
              >
                {finding.file}
              </code>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default function FindingsList({ findings }) {
  if (!findings.length) {
    return (
      <div
        className="text-center py-8 rounded-lg border"
        style={{ background: 'var(--charcoal-800)', borderColor: 'var(--navy-700)' }}
      >
        <ShieldCheck size={28} className="mx-auto mb-2" style={{ color: '#4ade80' }} />
        <p className="text-sm" style={{ color: 'var(--slate-400)' }}>
          No risk findings detected
        </p>
      </div>
    )
  }

  return (
    <section>
      <h3
        className="text-sm font-semibold mb-3 uppercase tracking-wider flex items-center gap-2"
        style={{ color: 'var(--slate-400)' }}
      >
        <Info size={14} />
        Findings ({findings.length})
      </h3>
      <div className="space-y-2">
        {findings.map((f, i) => (
          <Finding key={i} finding={f} />
        ))}
      </div>
    </section>
  )
}

