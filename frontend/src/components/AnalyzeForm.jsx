import { useState } from 'react'
import { Search, Loader2 } from 'lucide-react'

export default function AnalyzeForm({ onAnalyze, loading }) {
  const [url, setUrl] = useState('')

  function handleSubmit(e) {
    e.preventDefault()
    const trimmed = url.trim()
    if (trimmed) onAnalyze(trimmed)
  }

  return (
    <form onSubmit={handleSubmit} className="mb-6">
      <label
        htmlFor="pr-url"
        className="block text-sm font-medium mb-2"
        style={{ color: 'var(--slate-300)' }}
      >
        Analyze a Pull Request
      </label>
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
            style={{ color: 'var(--slate-400)' }}
          />
          <input
            id="pr-url"
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://github.com/owner/repo/pull/123"
            disabled={loading}
            required
            className="w-full pl-9 pr-3 py-2.5 rounded-lg text-sm border transition-colors"
            style={{
              background: 'var(--charcoal-800)',
              borderColor: 'var(--navy-700)',
              color: 'var(--slate-200)',
            }}
          />
        </div>
        <button
          type="submit"
          disabled={loading || !url.trim()}
          className="px-5 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          style={{
            background: 'var(--blue-600)',
            color: 'white',
          }}
        >
          {loading ? (
            <>
              <Loader2 size={16} className="animate-spin" />
              Analyzing…
            </>
          ) : (
            'Analyze'
          )}
        </button>
      </div>
    </form>
  )
}

