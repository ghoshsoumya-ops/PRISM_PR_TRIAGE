import { useState } from 'react'
import './index.css'
import Header from './components/Header'
import AnalyzeForm from './components/AnalyzeForm'
import Report from './components/Report'
import EmptyState from './components/EmptyState'
import ErrorMessage from './components/ErrorMessage'
import { analyzepr } from './services/api'

export default function App() {
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleAnalyze(url) {
    setLoading(true)
    setError(null)
    setReport(null)
    try {
      const data = await analyzepr(url)
      setReport(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen" style={{ background: 'var(--navy-950)' }}>
      <Header />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
        <AnalyzeForm onAnalyze={handleAnalyze} loading={loading} />
        {error && <ErrorMessage message={error} onDismiss={() => setError(null)} />}
        {report && <Report data={report} />}
        {!report && !loading && !error && <EmptyState />}
      </main>
    </div>
  )
}
