import { Sparkles, AlertCircle, Ban } from 'lucide-react'

export default function AISummary({ summary, status }) {
  if (status === 'disabled') return null

  if (status === 'unavailable') {
    return (
      <section
        className="px-4 py-3 rounded-lg border"
        style={{ background: 'var(--charcoal-800)', borderColor: 'var(--navy-700)' }}
      >
        <div className="flex items-center gap-2 text-sm" style={{ color: 'var(--slate-400)' }}>
          <Ban size={14} />
          <span>
            AI summary unavailable — configure <code className="text-xs">GOOGLE_AI_API_KEY</code> to enable Gemma 4 analysis
          </span>
        </div>
      </section>
    )
  }

  if (status === 'error') {
    return (
      <section
        className="px-4 py-3 rounded-lg border"
        style={{ background: '#1c1517', borderColor: '#5c2d2d' }}
      >
        <div className="flex items-center gap-2 text-sm" style={{ color: '#d4a0a0' }}>
          <AlertCircle size={14} />
          <span>AI analysis encountered an error. Deterministic findings are shown above.</span>
        </div>
      </section>
    )
  }

  if (!summary) return null

  return (
    <section>
      <h3
        className="text-sm font-semibold mb-3 uppercase tracking-wider flex items-center gap-2"
        style={{ color: 'var(--slate-400)' }}
      >
        <Sparkles size={14} style={{ color: 'var(--blue-400)' }} />
        AI Analysis
        <span
          className="text-[10px] font-normal normal-case tracking-normal px-1.5 py-0.5 rounded"
          style={{ background: 'var(--navy-700)', color: 'var(--blue-400)' }}
        >
          Gemma 4
        </span>
      </h3>
      <div
        className="px-4 py-3 rounded-lg border text-sm leading-relaxed whitespace-pre-wrap"
        style={{
          background: 'var(--charcoal-800)',
          borderColor: 'var(--navy-700)',
          color: 'var(--slate-300)',
        }}
      >
        {summary}
      </div>
      <p
        className="text-[11px] mt-2 italic"
        style={{ color: 'var(--slate-400)' }}
      >
        AI-generated content — verify independently before acting on these insights
      </p>
    </section>
  )
}

