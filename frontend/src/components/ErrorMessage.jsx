import { AlertCircle, X } from 'lucide-react'

export default function ErrorMessage({ message, onDismiss }) {
  return (
    <div
      className="mb-6 px-4 py-3 rounded-lg border flex items-start gap-3"
      style={{
        background: '#1c1517',
        borderColor: '#5c2d2d',
      }}
      role="alert"
    >
      <AlertCircle size={18} className="mt-0.5 shrink-0" style={{ color: 'var(--red-500)' }} />
      <div className="flex-1">
        <p className="text-sm font-medium" style={{ color: '#fca5a5' }}>
          Analysis failed
        </p>
        <p className="text-sm mt-0.5" style={{ color: '#d4a0a0' }}>
          {message}
        </p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="shrink-0 p-1 rounded cursor-pointer"
          style={{ color: '#d4a0a0' }}
          aria-label="Dismiss error"
        >
          <X size={16} />
        </button>
      )}
    </div>
  )
}

