import {
  GitPullRequest,
  User,
  GitBranch,
  FileDiff,
  Clock,
  Copy,
  Check,
} from 'lucide-react'
import { useState } from 'react'
import FindingsList from './FindingsList'
import AISummary from './AISummary'

const LEVEL_STYLES = {
  low: { bg: '#0f2918', border: '#1a5c32', text: '#4ade80', label: 'Low Risk' },
  medium: { bg: '#1c1a0f', border: '#5c4d1a', text: '#facc15', label: 'Medium Risk' },
  high: { bg: '#1c150f', border: '#5c381a', text: '#fb923c', label: 'High Risk' },
  critical: { bg: '#1c0f0f', border: '#5c1a1a', text: '#f87171', label: 'Critical Risk' },
}

function ScoreBadge({ score, level }) {
  const style = LEVEL_STYLES[level] || LEVEL_STYLES.low
  return (
    <div
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-semibold border"
      style={{ background: style.bg, borderColor: style.border, color: style.text }}
    >
      <span className="text-xl tabular-nums">{score}</span>
      <span className="text-xs font-medium opacity-80">/100</span>
      <span className="text-xs ml-1 uppercase tracking-wide">{style.label}</span>
    </div>
  )
}

function PRMeta({ pr }) {
  return (
    <div
      className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm"
      style={{ color: 'var(--slate-400)' }}
    >
      <div className="flex items-center gap-2">
        <User size={14} />
        <span>{pr.author}</span>
      </div>
      <div className="flex items-center gap-2">
        <GitBranch size={14} />
        <span className="truncate" title={`${pr.head_branch} → ${pr.base_branch}`}>
          {pr.head_branch} → {pr.base_branch}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <FileDiff size={14} />
        <span>
          <span style={{ color: '#4ade80' }}>+{pr.additions.toLocaleString()}</span>
          {' / '}
          <span style={{ color: '#f87171' }}>−{pr.deletions.toLocaleString()}</span>
          {' · '}
          {pr.changed_files} files
        </span>
      </div>
      <div className="flex items-center gap-2">
        <Clock size={14} />
        <span>{new Date(pr.created_at).toLocaleDateString()}</span>
      </div>
      <div className="flex items-center gap-2">
        <GitPullRequest size={14} />
        <span className="capitalize">{pr.state}</span>
      </div>
    </div>
  )
}

function Recommendations({ items }) {
  if (!items.length) return null
  return (
    <section>
      <h3
        className="text-sm font-semibold mb-3 uppercase tracking-wider"
        style={{ color: 'var(--slate-400)' }}
      >
        Recommendations
      </h3>
      <ul className="space-y-2">
        {items.map((rec, i) => (
          <li
            key={i}
            className="text-sm pl-4 border-l-2"
            style={{ borderColor: 'var(--blue-600)', color: 'var(--slate-300)' }}
          >
            {rec}
          </li>
        ))}
      </ul>
    </section>
  )
}

export default function Report({ data }) {
  const [copied, setCopied] = useState(false)

  function copyReport() {
    const lines = [
      `PRism Report — ${data.pull_request.repo}#${data.pull_request.number}`,
      `Title: ${data.pull_request.title}`,
      `Risk: ${data.risk_score}/100 (${data.risk_level})`,
      '',
      'Findings:',
      ...data.findings.map(
        (f) => `  [${f.severity.toUpperCase()}] ${f.title}: ${f.description}`
      ),
      '',
      'Recommendations:',
      ...data.recommendations.map((r) => `  • ${r}`),
    ]
    if (data.ai_summary) {
      lines.push('', 'AI Summary (Gemma 4):', data.ai_summary)
    }
    navigator.clipboard.writeText(lines.join('\n')).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  return (
    <div
      className="rounded-lg border overflow-hidden"
      style={{ background: 'var(--charcoal-900)', borderColor: 'var(--navy-700)' }}
    >
      {/* Header */}
      <div
        className="px-5 py-4 border-b flex flex-wrap items-start justify-between gap-3"
        style={{ borderColor: 'var(--navy-700)' }}
      >
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 mb-1">
            <GitPullRequest size={16} style={{ color: 'var(--blue-400)' }} />
            <a
              href={data.pull_request.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-semibold hover:underline truncate"
              style={{ color: 'var(--slate-200)' }}
            >
              {data.pull_request.repo}#{data.pull_request.number}
            </a>
          </div>
          <h2
            className="text-base font-medium mb-3"
            style={{ color: 'var(--slate-200)' }}
          >
            {data.pull_request.title}
          </h2>
          <PRMeta pr={data.pull_request} />
        </div>
        <div className="flex items-center gap-2">
          <ScoreBadge score={data.risk_score} level={data.risk_level} />
          <button
            onClick={copyReport}
            className="p-2 rounded-lg border cursor-pointer transition-colors"
            style={{
              background: 'var(--charcoal-800)',
              borderColor: 'var(--navy-700)',
              color: 'var(--slate-400)',
            }}
            title="Copy report"
            aria-label="Copy report to clipboard"
          >
            {copied ? <Check size={16} /> : <Copy size={16} />}
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="px-5 py-5 space-y-6">
        <FindingsList findings={data.findings} />
        <AISummary summary={data.ai_summary} status={data.ai_status} />
        <Recommendations items={data.recommendations} />
      </div>
    </div>
  )
}

