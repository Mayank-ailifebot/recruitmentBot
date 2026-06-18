import { useEffect, useState } from 'react'

interface HealthStatus {
  status: string
  service: string
  timestamp: string
}

function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/v1/health')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then((data) => setHealth(data))
      .catch((err) => setError(err.message))
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center p-8">
      {/* Background gradient orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-secondary/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      {/* Main Card */}
      <div className="glass rounded-2xl p-10 max-w-lg w-full text-center relative z-10 shadow-glow">
        {/* Logo / Title */}
        <div className="mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-xl bg-primary/20 mb-4">
            <svg className="w-8 h-8 text-primary-light" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h1 className="text-4xl font-bold font-display gradient-text mb-2">
            RecruitBot
          </h1>
          <p className="text-text-secondary text-sm">
            Agentic Recruitment Orchestrator
          </p>
        </div>

        {/* Connection Status */}
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-text-primary">
            System Status
          </h2>

          {/* Frontend Status */}
          <div className="flex items-center justify-between py-3 px-4 rounded-lg bg-surface-700/50">
            <span className="text-text-secondary text-sm">Frontend (Vite + React)</span>
            <span className="inline-flex items-center gap-1.5 text-success text-sm font-medium">
              <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
              Online
            </span>
          </div>

          {/* Backend Status */}
          <div className="flex items-center justify-between py-3 px-4 rounded-lg bg-surface-700/50">
            <span className="text-text-secondary text-sm">Backend (FastAPI)</span>
            {health ? (
              <span className="inline-flex items-center gap-1.5 text-success text-sm font-medium">
                <span className="w-2 h-2 rounded-full bg-success animate-pulse" />
                {health.status}
              </span>
            ) : error ? (
              <span className="inline-flex items-center gap-1.5 text-error text-sm font-medium">
                <span className="w-2 h-2 rounded-full bg-error" />
                {error}
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-warning text-sm font-medium">
                <span className="w-2 h-2 rounded-full bg-warning animate-pulse" />
                Connecting...
              </span>
            )}
          </div>

          {/* Database Status */}
          <div className="flex items-center justify-between py-3 px-4 rounded-lg bg-surface-700/50">
            <span className="text-text-secondary text-sm">Database (PostgreSQL)</span>
            <span className="inline-flex items-center gap-1.5 text-text-muted text-sm font-medium">
              <span className="w-2 h-2 rounded-full bg-surface-400" />
              Phase 0.2
            </span>
          </div>

          {/* LLM Status */}
          <div className="flex items-center justify-between py-3 px-4 rounded-lg bg-surface-700/50">
            <span className="text-text-secondary text-sm">LLM Gateway (Claude)</span>
            <span className="inline-flex items-center gap-1.5 text-text-muted text-sm font-medium">
              <span className="w-2 h-2 rounded-full bg-surface-400" />
              Phase 0.3
            </span>
          </div>
        </div>

        {/* Timestamp */}
        {health && (
          <p className="mt-6 text-xs text-text-muted">
            Last check: {new Date(health.timestamp).toLocaleString()}
          </p>
        )}

        {/* Phase Indicator */}
        <div className="mt-8 pt-6 border-t border-surface-600">
          <p className="text-xs text-text-muted">
            Phase 0 — Foundation & Platform Spine
          </p>
        </div>
      </div>
    </div>
  )
}

export default App
