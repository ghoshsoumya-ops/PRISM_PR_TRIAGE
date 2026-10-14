import { Shield } from 'lucide-react'

export default function Header() {
  return (
    <header
      className="border-b px-4 sm:px-6"
      style={{
        background: 'var(--navy-900)',
        borderColor: 'var(--navy-700)',
      }}
    >
      <div className="max-w-4xl mx-auto h-14 flex items-center gap-3">
        <Shield size={22} style={{ color: 'var(--blue-500)' }} />
        <h1
          className="text-lg font-semibold tracking-tight"
          style={{ color: 'var(--slate-200)' }}
        >
          PRism
        </h1>
        <span
          className="text-xs px-2 py-0.5 rounded-full"
          style={{
            background: 'var(--navy-700)',
            color: 'var(--slate-400)',
          }}
        >
          PR Risk Triage
        </span>
      </div>
    </header>
  )
}

