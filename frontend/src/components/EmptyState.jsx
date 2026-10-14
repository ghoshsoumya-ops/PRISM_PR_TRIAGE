import { Shield } from 'lucide-react'

export default function EmptyState() {
  return (
    <div
      className="text-center py-20 rounded-lg border"
      style={{
        background: 'var(--charcoal-900)',
        borderColor: 'var(--navy-700)',
      }}
    >
      <Shield
        size={40}
        className="mx-auto mb-4"
        style={{ color: 'var(--navy-700)' }}
      />
      <p className="text-sm" style={{ color: 'var(--slate-400)' }}>
        Enter a GitHub pull request URL to begin analysis
      </p>
    </div>
  )
}

