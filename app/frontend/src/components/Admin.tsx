/**
 * Admin interface — correction review, feedback history, training data export.
 *
 * Access is gated by VITE_ADMIN_PASSWORD. This is not production security —
 * it prevents casual access only. All actual data access goes through the
 * same API as the rest of the app.
 *
 * Three tabs: Review | History | Export
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  getPendingFeedback, getAllFeedback,
  approveFeedback, rejectFeedback, downloadTrainingData,
  getSyncStatus, downloadContributions, reseedFromCanonical, getPendingContributions,
  uploadContributionZip, approveContribution, rejectContribution,
} from '../services/api'
import type { FeedbackRecord, FeedbackFilters, SyncStatus, PendingContribution, UploadedContribution } from '../services/api'

const ADMIN_PASSWORD = import.meta.env.VITE_ADMIN_PASSWORD as string | undefined

// ─── Auth gate ────────────────────────────────────────────────────────────────

function PasswordGate({ onUnlock }: { onUnlock: () => void }) {
  const [value, setValue] = useState('')
  const [error, setError] = useState(false)

  const attempt = () => {
    if (!ADMIN_PASSWORD || value === ADMIN_PASSWORD) {
      onUnlock()
    } else {
      setError(true)
      setValue('')
    }
  }

  return (
    <div style={{
      height: '100%', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center', padding: '2rem', gap: '1rem',
    }}>
      <div className="font-display" style={{ fontSize: '1.5rem', color: 'var(--amber)', fontStyle: 'italic' }}>
        Admin access
      </div>
      <input
        className="input"
        type="password"
        value={value}
        onChange={(e) => { setValue(e.target.value); setError(false) }}
        onKeyDown={(e) => e.key === 'Enter' && attempt()}
        placeholder="Password"
        autoFocus
        style={{ maxWidth: 280, textAlign: 'center' }}
      />
      {error && (
        <p style={{ fontSize: '0.78rem', color: 'var(--terra-light)' }}>Incorrect password</p>
      )}
      <button className="btn-amber" onClick={attempt}>
        Enter
      </button>
    </div>
  )
}

// ─── Shared UI ────────────────────────────────────────────────────────────────

const AUTHORITY_LABELS: Record<number, string> = {
  1: 'Native', 2: 'Academic', 3: 'Community', 4: 'Inferred',
}
const AUTHORITY_COLORS: Record<number, string> = {
  1: 'var(--amber)', 2: '#7eb8c9', 3: 'var(--text-muted)', 4: 'var(--text-dim)',
}

function AuthBadge({ level }: { level: number }) {
  return (
    <span style={{
      fontSize: '0.63rem', fontWeight: 700, letterSpacing: '0.08em',
      textTransform: 'uppercase', color: AUTHORITY_COLORS[level],
      border: `1px solid ${AUTHORITY_COLORS[level]}`,
      borderRadius: 3, padding: '0.1rem 0.35rem', whiteSpace: 'nowrap',
    }}>
      {AUTHORITY_LABELS[level] ?? `L${level}`}
    </span>
  )
}

function RatingChip({ rating }: { rating: string }) {
  const isUp = rating === 'thumbs_up'
  return (
    <span style={{
      fontSize: '0.72rem', padding: '0.15rem 0.5rem',
      borderRadius: 4, fontWeight: 600,
      background: isUp ? 'rgba(46,160,67,0.15)' : 'rgba(193,68,14,0.15)',
      color: isUp ? '#4caf76' : 'var(--terra-light)',
    }}>
      {isUp ? '👍 Up' : '👎 Down'}
    </span>
  )
}

function formatDate(ts: string) {
  return new Date(ts).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

function truncate(str: string | undefined, n: number) {
  if (!str) return ''
  return str.length > n ? str.slice(0, n) + '…' : str
}

// ─── Review Tab ───────────────────────────────────────────────────────────────

function ReviewTab() {
  const [records, setRecords] = useState<FeedbackRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [acting, setActing] = useState<Record<string, 'approving' | 'rejecting'>>({})
  const [done, setDone] = useState<Record<string, 'approved' | 'rejected'>>({})
  const [expanded, setExpanded] = useState<string | null>(null)
  const [editingLevel, setEditingLevel] = useState<Record<string, number>>({})

  const load = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      setRecords(await getPendingFeedback())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const handleApprove = async (id: string) => {
    setActing((a) => ({ ...a, [id]: 'approving' }))
    try {
      await approveFeedback(id, editingLevel[id])
      setDone((d) => ({ ...d, [id]: 'approved' }))
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Approve failed')
    } finally {
      setActing((a) => { const n = { ...a }; delete n[id]; return n })
    }
  }

  const handleReject = async (id: string) => {
    setActing((a) => ({ ...a, [id]: 'rejecting' }))
    try {
      await rejectFeedback(id)
      setDone((d) => ({ ...d, [id]: 'rejected' }))
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Reject failed')
    } finally {
      setActing((a) => { const n = { ...a }; delete n[id]; return n })
    }
  }

  if (loading) return <EmptyState text="Loading…" />
  if (error) return <EmptyState text={error} warn />
  if (records.length === 0) return <EmptyState text="No pending corrections" />

  const pending = records.filter((r) => !done[r.id])

  return (
    <div>
      <div style={{ padding: '0.5rem 1rem 0.25rem', fontSize: '0.75rem', color: 'var(--text-dim)' }}>
        {pending.length} pending · {Object.keys(done).length} actioned this session
      </div>
      {records.map((rec) => {
        const isDone = !!done[rec.id]
        const isActing = !!acting[rec.id]
        return (
          <div
            key={rec.id}
            style={{
              borderBottom: '1px solid var(--border)',
              padding: '0.85rem 1rem',
              opacity: isDone ? 0.45 : 1,
              transition: 'opacity 0.3s',
            }}
          >
            {/* Header row */}
            <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap', marginBottom: '0.5rem' }}>
              <RatingChip rating={rec.rating} />
              <AuthBadge level={rec.authority_level} />
              <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)', marginLeft: 'auto' }}>
                {formatDate(rec.timestamp)}
              </span>
            </div>

            {/* Original interaction */}
            {rec.interaction && (
              <div style={{ marginBottom: '0.5rem' }}>
                <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginBottom: '0.15rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  User asked
                </p>
                <p style={{ fontSize: '0.83rem', color: 'var(--text-muted)' }}>
                  {truncate(rec.interaction.user_message, 120)}
                </p>
              </div>
            )}

            {/* LLM response */}
            {rec.interaction && (
              <div style={{ marginBottom: '0.5rem' }}>
                <button
                  onClick={() => setExpanded(expanded === rec.id ? null : rec.id)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.72rem', color: 'var(--text-dim)', padding: 0, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: '0.15rem', display: 'block' }}
                >
                  Ading's response {expanded === rec.id ? '▲' : '▼'}
                </button>
                {expanded === rec.id && (
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)', fontStyle: 'italic', animation: 'pageEnter 0.2s ease forwards' }}>
                    {rec.interaction.llm_response}
                  </p>
                )}
              </div>
            )}

            {/* Correction */}
            {(rec.correction_kapampangan || rec.correction_english) && (
              <div style={{
                padding: '0.5rem 0.75rem',
                background: 'var(--bg-2)', borderRadius: 6,
                border: '1px solid var(--border)', marginBottom: '0.6rem',
              }}>
                <p style={{ fontSize: '0.68rem', color: 'var(--amber-dim)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '0.2rem' }}>
                  Proposed correction
                </p>
                {rec.correction_kapampangan && (
                  <p className="font-display" style={{ fontStyle: 'italic', color: 'var(--amber)', fontSize: '1rem', margin: 0 }}>
                    {rec.correction_kapampangan}
                  </p>
                )}
                {rec.correction_english && (
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0 }}>
                    {rec.correction_english}
                  </p>
                )}
                {rec.correction_note && (
                  <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.25rem', fontStyle: 'italic' }}>
                    {rec.correction_note}
                  </p>
                )}
              </div>
            )}

            {/* Authority level override */}
            {!isDone && rec.correction_kapampangan && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.6rem' }}>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Authority level:</span>
                {[1, 2, 3, 4].map((lvl) => (
                  <button
                    key={lvl}
                    onClick={() => setEditingLevel((e) => ({ ...e, [rec.id]: lvl }))}
                    style={{
                      background: 'none', border: `1px solid ${(editingLevel[rec.id] ?? rec.authority_level) === lvl ? AUTHORITY_COLORS[lvl] : 'var(--border)'}`,
                      color: (editingLevel[rec.id] ?? rec.authority_level) === lvl ? AUTHORITY_COLORS[lvl] : 'var(--text-dim)',
                      borderRadius: 4, padding: '0.1rem 0.5rem',
                      fontSize: '0.7rem', cursor: 'pointer', fontWeight: 600,
                    }}
                  >
                    {lvl}
                  </button>
                ))}
              </div>
            )}

            {/* Actions */}
            {isDone ? (
              <p style={{ fontSize: '0.75rem', color: done[rec.id] === 'approved' ? '#4caf76' : 'var(--terra-light)', fontWeight: 600 }}>
                {done[rec.id] === 'approved' ? '✓ Approved' : '✗ Rejected'}
              </p>
            ) : (
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button
                  className="btn-amber"
                  onClick={() => handleApprove(rec.id)}
                  disabled={isActing}
                  style={{ fontSize: '0.78rem', padding: '0.35rem 0.9rem' }}
                >
                  {acting[rec.id] === 'approving' ? 'Approving…' : 'Approve'}
                </button>
                <button
                  className="btn-ghost"
                  onClick={() => handleReject(rec.id)}
                  disabled={isActing}
                  style={{ fontSize: '0.78rem', padding: '0.35rem 0.9rem', borderColor: 'var(--terra)', color: 'var(--terra-light)' }}
                >
                  {acting[rec.id] === 'rejecting' ? 'Rejecting…' : 'Reject'}
                </button>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

// ─── History Tab ──────────────────────────────────────────────────────────────

function HistoryTab() {
  const [records, setRecords] = useState<FeedbackRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [filters, setFilters] = useState<FeedbackFilters>({})
  const [expanded, setExpanded] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      setRecords(await getAllFeedback(filters))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed')
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => { load() }, [load])

  return (
    <div>
      {/* Filter bar */}
      <div style={{ padding: '0.75rem 1rem', display: 'flex', gap: '0.5rem', flexWrap: 'wrap', borderBottom: '1px solid var(--border)' }}>
        {/* Rating */}
        {(['', 'thumbs_up', 'thumbs_down'] as const).map((r) => (
          <button
            key={r}
            className={`tab-pill${filters.rating === r || (!filters.rating && r === '') ? ' active' : ''}`}
            onClick={() => setFilters((f) => ({ ...f, rating: r || undefined }))}
            style={{ fontSize: '0.72rem' }}
          >
            {r === '' ? 'All' : r === 'thumbs_up' ? '👍' : '👎'}
          </button>
        ))}
        <div style={{ width: 1, background: 'var(--border)', margin: '0 0.25rem' }} />
        {/* Applied */}
        {([undefined, true, false] as const).map((a, i) => (
          <button
            key={i}
            className={`tab-pill${filters.applied === a ? ' active' : ''}`}
            onClick={() => setFilters((f) => ({ ...f, applied: a }))}
            style={{ fontSize: '0.72rem' }}
          >
            {a === undefined ? 'All' : a ? 'Applied' : 'Not applied'}
          </button>
        ))}
        <div style={{ width: 1, background: 'var(--border)', margin: '0 0.25rem' }} />
        {/* Authority */}
        {([undefined, 1, 2, 3, 4] as const).map((lvl, i) => (
          <button
            key={i}
            className={`tab-pill${filters.authority_level === lvl ? ' active' : ''}`}
            onClick={() => setFilters((f) => ({ ...f, authority_level: lvl }))}
            style={{ fontSize: '0.72rem' }}
          >
            {lvl === undefined ? 'Any level' : `L${lvl}`}
          </button>
        ))}
      </div>

      {loading && <EmptyState text="Loading…" />}
      {error && <EmptyState text={error} warn />}
      {!loading && !error && records.length === 0 && <EmptyState text="No records" />}

      {records.map((rec) => (
        <div key={rec.id} style={{ borderBottom: '1px solid var(--border)', padding: '0.75rem 1rem' }}>
          <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center', flexWrap: 'wrap', marginBottom: '0.35rem' }}>
            <RatingChip rating={rec.rating} />
            <AuthBadge level={rec.authority_level} />
            {rec.reviewed && (
              <span style={{
                fontSize: '0.63rem', padding: '0.1rem 0.4rem',
                borderRadius: 4, border: '1px solid var(--border)',
                color: rec.applied ? '#4caf76' : 'var(--text-dim)',
              }}>
                {rec.applied ? 'Applied' : 'Rejected'}
              </span>
            )}
            <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)', marginLeft: 'auto' }}>
              {formatDate(rec.timestamp)}
            </span>
          </div>

          {rec.interaction && (
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '0 0 0.3rem' }}>
              {truncate(rec.interaction.user_message, 100)}
            </p>
          )}

          {(rec.correction_kapampangan || rec.correction_english) && (
            <p className="font-display" style={{ fontStyle: 'italic', color: 'var(--amber)', fontSize: '0.9rem', margin: 0 }}>
              → {rec.correction_kapampangan || rec.correction_english}
            </p>
          )}

          {/* Expand row for full context */}
          {rec.interaction && (
            <>
              <button
                onClick={() => setExpanded(expanded === rec.id ? null : rec.id)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '0.68rem', color: 'var(--text-dim)', padding: '0.25rem 0 0' }}
              >
                {expanded === rec.id ? '▲ less' : '▼ full context'}
              </button>
              {expanded === rec.id && (
                <div style={{
                  marginTop: '0.4rem', padding: '0.5rem 0.75rem',
                  background: 'var(--bg-2)', borderRadius: 6,
                  animation: 'pageEnter 0.2s ease forwards',
                }}>
                  <p style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginBottom: '0.25rem' }}>
                    Model: {rec.interaction.model}
                  </p>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontStyle: 'italic', margin: 0 }}>
                    {rec.interaction.llm_response}
                  </p>
                  {rec.correction_note && (
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '0.35rem' }}>
                      Note: {rec.correction_note}
                    </p>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      ))}
    </div>
  )
}

// ─── Export Tab ───────────────────────────────────────────────────────────────

function ExportTab() {
  const [format, setFormat] = useState<'sft' | 'dpo'>('sft')
  const [minLevel, setMinLevel] = useState(1)
  const [after, setAfter] = useState('')
  const [before, setBefore] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleExport = async () => {
    setLoading(true)
    setError(null)
    setSuccess(false)
    try {
      await downloadTrainingData(format, minLevel, after || undefined, before || undefined)
      setSuccess(true)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Export failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '1rem' }}>
      <p style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginBottom: '1.25rem' }}>
        Export reviewed and applied feedback as JSONL training data. Only feedback with
        reviewed=true and applied=true is included.
      </p>

      {/* Format */}
      <div style={{ marginBottom: '1rem' }}>
        <label style={labelStyle}>Format</label>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {(['sft', 'dpo'] as const).map((f) => (
            <button
              key={f}
              className={`tab-pill${format === f ? ' active' : ''}`}
              onClick={() => setFormat(f)}
            >
              {f.toUpperCase()}
            </button>
          ))}
        </div>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '0.3rem' }}>
          {format === 'sft'
            ? 'SFT — {prompt, response} pairs. Thumbs-up uses original; thumbs-down uses correction.'
            : 'DPO — {prompt, chosen, rejected} triples. Requires thumbs-down with correction.'}
        </p>
      </div>

      {/* Min authority level */}
      <div style={{ marginBottom: '1rem' }}>
        <label style={labelStyle}>Min authority level (≤ N included)</label>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {[1, 2, 3, 4].map((lvl) => (
            <button
              key={lvl}
              className={`tab-pill${minLevel === lvl ? ' active' : ''}`}
              onClick={() => setMinLevel(lvl)}
              style={{ color: minLevel === lvl ? AUTHORITY_COLORS[lvl] : undefined }}
            >
              {lvl} — {AUTHORITY_LABELS[lvl]}
            </button>
          ))}
        </div>
      </div>

      {/* Date range */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginBottom: '1.25rem' }}>
        <div>
          <label style={labelStyle}>After date</label>
          <input className="input" type="date" value={after} onChange={(e) => setAfter(e.target.value)} />
        </div>
        <div>
          <label style={labelStyle}>Before date</label>
          <input className="input" type="date" value={before} onChange={(e) => setBefore(e.target.value)} />
        </div>
      </div>

      {error && <p style={{ fontSize: '0.8rem', color: 'var(--terra-light)', marginBottom: '0.75rem' }}>{error}</p>}
      {success && <p style={{ fontSize: '0.8rem', color: '#4caf76', marginBottom: '0.75rem' }}>✓ Download started</p>}

      <button
        className="btn-amber"
        onClick={handleExport}
        disabled={loading}
        style={{ width: '100%', justifyContent: 'center' }}
      >
        {loading ? 'Preparing…' : `Download ${format.toUpperCase()} JSONL`}
      </button>
    </div>
  )
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function EmptyState({ text, warn = false }: { text: string; warn?: boolean }) {
  return (
    <div style={{ padding: '2rem 1rem', textAlign: 'center', color: warn ? 'var(--terra-light)' : 'var(--text-dim)', fontSize: '0.82rem' }}>
      {text}
    </div>
  )
}

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: '0.7rem', fontWeight: 700,
  letterSpacing: '0.08em', textTransform: 'uppercase',
  color: 'var(--text-dim)', marginBottom: '0.4rem',
}

// ─── Contributions Tab ────────────────────────────────────────────────────────

type ContribSubTab = 'incoming' | 'sync'

function SyncStatusView() {
  const [status, setStatus] = useState<SyncStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)
  const [exportDone, setExportDone] = useState(false)
  const [exportError, setExportError] = useState<string | null>(null)
  const [minLevel, setMinLevel] = useState(1)
  const [reseedConfirm, setReseedConfirm] = useState(false)
  const [reseeding, setReseeding] = useState(false)
  const [reseedResult, setReseedResult] = useState<{ vocabulary: number; grammar_nodes: number } | null>(null)
  const [reseedError, setReseedError] = useState<string | null>(null)

  useEffect(() => {
    getSyncStatus()
      .then(setStatus)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const handleReseed = async () => {
    setReseeding(true)
    setReseedError(null)
    setReseedResult(null)
    setReseedConfirm(false)
    try {
      const result = await reseedFromCanonical()
      setReseedResult(result)
      // Refresh status counts
      getSyncStatus().then(setStatus).catch(() => {})
    } catch (e) {
      setReseedError(e instanceof Error ? e.message : 'Reseed failed')
    } finally {
      setReseeding(false)
    }
  }

  const handleExport = async () => {
    if (!status) return
    setExporting(true)
    setExportError(null)
    setExportDone(false)
    try {
      await downloadContributions(status.contributor_name, minLevel)
      setExportDone(true)
    } catch (e) {
      setExportError(e instanceof Error ? e.message : 'Export failed')
    } finally {
      setExporting(false)
    }
  }

  if (loading) return <EmptyState text="Loading…" />
  if (error) return <EmptyState text={error} warn />
  if (!status) return null

  const modeLabel: Record<string, string> = {
    git: 'Git (default) — canonical files in this repository',
    sync: 'Maintainer sync — hosted canonical URL',
    shared_db: 'Shared database — real-time sync',
  }

  return (
    <div style={{ padding: '1rem' }}>
      <div style={{ display: 'grid', gap: '0.9rem', marginBottom: '1.5rem' }}>
        {/* Mode */}
        <div style={statCard}>
          <p style={statLabel}>Knowledge sharing mode</p>
          <p style={statValue}>{modeLabel[status.mode] ?? status.mode}</p>
        </div>

        {/* Last seeded */}
        <div style={statCard}>
          <p style={statLabel}>Last seeded from canonical files</p>
          <p style={statValue}>
            {status.last_seeded
              ? new Date(status.last_seeded).toLocaleString()
              : 'Never — database is empty or was not seeded from files'}
          </p>
        </div>

        {/* Seeded count */}
        <div style={statCard}>
          <p style={statLabel}>Seeded entries</p>
          <p style={statValue}>{status.seeded_count.vocabulary} vocabulary</p>
        </div>

        {/* Local additions */}
        <div style={statCard}>
          <p style={statLabel}>Local additions (not in canonical files)</p>
          <p style={statValue}>
            {status.local_additions.vocabulary} vocabulary ·{' '}
            {status.local_additions.grammar_nodes} grammar nodes
          </p>
        </div>

        {status.canonical_url && (
          <div style={statCard}>
            <p style={statLabel}>Canonical URL (Mode 2)</p>
            <p style={{ ...statValue, fontFamily: 'monospace', fontSize: '0.78rem' }}>
              {status.canonical_url}
            </p>
          </div>
        )}
      </div>

      {/* Export contributions */}
      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem' }}>
        <p style={{ ...labelStyle, marginBottom: '0.5rem' }}>Export my contributions</p>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)' }}>Min authority level:</span>
          {[1, 2, 3, 4].map((lvl) => (
            <button
              key={lvl}
              className={`tab-pill${minLevel === lvl ? ' active' : ''}`}
              onClick={() => setMinLevel(lvl)}
              style={{ fontSize: '0.72rem' }}
            >
              {lvl}
            </button>
          ))}
        </div>
        {exportError && <p style={{ fontSize: '0.78rem', color: 'var(--terra-light)', marginBottom: '0.5rem' }}>{exportError}</p>}
        {exportDone && <p style={{ fontSize: '0.78rem', color: '#4caf76', marginBottom: '0.5rem' }}>✓ Download started</p>}
        <button
          className="btn-amber"
          onClick={handleExport}
          disabled={exporting}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          {exporting ? 'Preparing zip…' : `Download contributions (Level ≤ ${minLevel})`}
        </button>

        <p style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '0.5rem' }}>
          Exports locally added vocabulary and grammar entries that are not in the canonical files.
          To contribute: send the zip to the maintainer or commit to a branch and open a pull request.
        </p>
      </div>

      {/* Force reseed */}
      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem', marginTop: '0.5rem' }}>
        <p style={{ ...labelStyle, marginBottom: '0.35rem' }}>Force reseed from canonical files</p>
        <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginBottom: '0.75rem' }}>
          Truncates the vocabulary and grammar tables and reloads them from the canonical data files.
          Local additions that have not been exported will be permanently lost.
        </p>

        {reseedResult && (
          <p style={{ fontSize: '0.78rem', color: '#4caf76', marginBottom: '0.5rem' }}>
            ✓ Reseeded: {reseedResult.vocabulary} vocabulary · {reseedResult.grammar_nodes} grammar nodes
          </p>
        )}
        {reseedError && (
          <p style={{ fontSize: '0.78rem', color: 'var(--terra-light)', marginBottom: '0.5rem' }}>{reseedError}</p>
        )}

        {!reseedConfirm ? (
          <button
            className="btn-ghost"
            onClick={() => setReseedConfirm(true)}
            disabled={reseeding}
            style={{ fontSize: '0.8rem' }}
          >
            Force reseed from canonical…
          </button>
        ) : (
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '0.78rem', color: 'var(--terra-light)' }}>
              This will delete all local additions. Are you sure?
            </span>
            <button
              className="btn-amber"
              onClick={handleReseed}
              disabled={reseeding}
              style={{ fontSize: '0.8rem', padding: '0.3rem 0.75rem' }}
            >
              {reseeding ? 'Reseeding…' : 'Yes, reseed now'}
            </button>
            <button
              className="btn-ghost"
              onClick={() => setReseedConfirm(false)}
              disabled={reseeding}
              style={{ fontSize: '0.8rem', padding: '0.3rem 0.75rem' }}
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

const statCard: React.CSSProperties = {
  background: 'var(--bg-2)', borderRadius: 6, padding: '0.65rem 0.85rem',
  border: '1px solid var(--border)',
}
const statLabel: React.CSSProperties = {
  fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase',
  letterSpacing: '0.08em', color: 'var(--text-dim)', marginBottom: '0.2rem',
}
const statValue: React.CSSProperties = {
  fontSize: '0.85rem', color: 'var(--text)',
}


function IncomingContributionsView() {
  const [pending, setPending] = useState<PendingContribution[]>([])
  const [uploaded, setUploaded] = useState<UploadedContribution | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [acting, setActing] = useState<Record<string, 'approving' | 'rejecting'>>({})
  const [done, setDone] = useState<Record<string, 'approved' | 'rejected'>>({})
  const [batchApproving, setBatchApproving] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    getPendingContributions()
      .then(setPending)
      .catch(() => {/* pending_contributions table may be empty — non-critical */})
  }, [])

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    setUploadError(null)
    setUploaded(null)
    try {
      setUploaded(await uploadContributionZip(file))
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  const handleApprove = async (id: string) => {
    setActing((a) => ({ ...a, [id]: 'approving' }))
    try {
      await approveContribution(id)
      setDone((d) => ({ ...d, [id]: 'approved' }))
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Approve failed')
    } finally {
      setActing((a) => { const n = { ...a }; delete n[id]; return n })
    }
  }

  const handleReject = async (id: string) => {
    setActing((a) => ({ ...a, [id]: 'rejecting' }))
    try {
      await rejectContribution(id)
      setDone((d) => ({ ...d, [id]: 'rejected' }))
    } catch (e) {
      alert(e instanceof Error ? e.message : 'Reject failed')
    } finally {
      setActing((a) => { const n = { ...a }; delete n[id]; return n })
    }
  }

  const handleBatchApproveLevel1 = async () => {
    const targets = pending.filter((c) => c.authority_level === 1 && !done[c.id])
    if (targets.length === 0) return
    setBatchApproving(true)
    for (const contrib of targets) {
      try {
        await approveContribution(contrib.id)
        setDone((d) => ({ ...d, [contrib.id]: 'approved' }))
      } catch {
        // Continue batch — individual failures do not abort the rest
      }
    }
    setBatchApproving(false)
  }

  return (
    <div style={{ padding: '1rem' }}>
      {/* Mode 2 — zip upload */}
      <div style={{ marginBottom: '1.5rem' }}>
        <p style={{ ...labelStyle, marginBottom: '0.5rem' }}>Upload contribution zip (Mode 2)</p>
        <div
          style={{
            border: '2px dashed var(--border)', borderRadius: 8,
            padding: '1.5rem', textAlign: 'center', cursor: 'pointer',
            transition: 'border-color 0.2s',
          }}
          onClick={() => fileRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault()
            const file = e.dataTransfer.files[0]
            if (file) {
              const input = fileRef.current
              if (input) {
                const dt = new DataTransfer()
                dt.items.add(file)
                input.files = dt.files
                input.dispatchEvent(new Event('change', { bubbles: true }))
              }
            }
          }}
        >
          <input
            ref={fileRef}
            type="file"
            accept=".zip"
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />
          <p style={{ fontSize: '0.85rem', color: 'var(--text-dim)' }}>
            {uploading ? 'Uploading…' : 'Drop a contribution .zip here or click to browse'}
          </p>
        </div>
        {uploadError && (
          <p style={{ fontSize: '0.78rem', color: 'var(--terra-light)', marginTop: '0.5rem' }}>{uploadError}</p>
        )}
      </div>

      {/* Uploaded contribution preview */}
      {uploaded && (
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ ...statCard, marginBottom: '0.75rem' }}>
            <p style={statLabel}>Contribution from: {String(uploaded.manifest.contributor ?? 'unknown')}</p>
            <p style={statValue}>
              {uploaded.counts.vocabulary} vocabulary · {uploaded.counts.grammar_nodes} nodes · {uploaded.counts.grammar_edges} edges
            </p>
            <p style={{ ...statValue, fontSize: '0.72rem', color: 'var(--text-dim)', marginTop: '0.25rem' }}>
              Exported: {uploaded.manifest.exported_at ? new Date(String(uploaded.manifest.exported_at)).toLocaleString() : '—'}
            </p>
          </div>

          <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', marginBottom: '0.5rem' }}>
            Review uploaded entries below. This preview does not write to the database.
            Use the scripts/import_knowledge.py CLI to import after merging via merge_contributions.py.
          </p>

          {uploaded.vocabulary.slice(0, 10).map((entry, i) => (
            <div key={i} style={{ borderBottom: '1px solid var(--border)', padding: '0.5rem 0' }}>
              <span className="font-display" style={{ fontStyle: 'italic', color: 'var(--amber)' }}>
                {String(entry.term ?? '')}
              </span>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginLeft: '0.5rem' }}>
                — {String(entry.meaning ?? '')}
              </span>
              <AuthBadge level={Number(entry.authority_level ?? 3)} />
            </div>
          ))}
          {uploaded.vocabulary.length > 10 && (
            <p style={{ fontSize: '0.72rem', color: 'var(--text-dim)', paddingTop: '0.5rem' }}>
              …and {uploaded.vocabulary.length - 10} more vocabulary entries
            </p>
          )}
        </div>
      )}

      {/* Mode 3 — pending contributions from shared DB */}
      {pending.length > 0 && (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
            <p style={{ ...labelStyle, margin: 0 }}>Pending contributions (Mode 3)</p>
            {pending.some((c) => c.authority_level === 1 && !done[c.id]) && (
              <button
                className="btn-amber"
                onClick={handleBatchApproveLevel1}
                disabled={batchApproving}
                style={{ fontSize: '0.75rem', padding: '0.2rem 0.65rem' }}
              >
                {batchApproving ? 'Approving…' : 'Approve all Level 1'}
              </button>
            )}
          </div>
          {pending.map((contrib) => {
            const isDone = !!done[contrib.id]
            return (
              <div key={contrib.id} style={{
                borderBottom: '1px solid var(--border)', padding: '0.75rem 0',
                opacity: isDone ? 0.45 : 1, transition: 'opacity 0.3s',
              }}>
                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.35rem' }}>
                  <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                    {contrib.contribution_type}
                  </span>
                  <AuthBadge level={contrib.authority_level} />
                  <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)', marginLeft: 'auto' }}>
                    {formatDate(contrib.submitted_at)} · {contrib.contributor}
                  </span>
                </div>

                {typeof contrib.payload === 'object' && contrib.payload && (
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                    {String((contrib.payload as Record<string, unknown>).term ?? (contrib.payload as Record<string, unknown>).id ?? '')}
                    {' — '}
                    {String((contrib.payload as Record<string, unknown>).meaning ?? '')}
                  </p>
                )}

                {isDone ? (
                  <p style={{ fontSize: '0.75rem', color: done[contrib.id] === 'approved' ? '#4caf76' : 'var(--terra-light)', fontWeight: 600 }}>
                    {done[contrib.id] === 'approved' ? '✓ Approved' : '✗ Rejected'}
                  </p>
                ) : (
                  <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.35rem' }}>
                    <button
                      className="btn-amber"
                      onClick={() => handleApprove(contrib.id)}
                      disabled={!!acting[contrib.id]}
                      style={{ fontSize: '0.75rem', padding: '0.25rem 0.7rem' }}
                    >
                      {acting[contrib.id] === 'approving' ? 'Approving…' : 'Approve'}
                    </button>
                    <button
                      className="btn-ghost"
                      onClick={() => handleReject(contrib.id)}
                      disabled={!!acting[contrib.id]}
                      style={{ fontSize: '0.75rem', padding: '0.25rem 0.7rem' }}
                    >
                      {acting[contrib.id] === 'rejecting' ? 'Rejecting…' : 'Reject'}
                    </button>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {pending.length === 0 && !uploaded && (
        <EmptyState text="No pending contributions. Upload a zip file (Mode 2) or wait for shared DB submissions (Mode 3)." />
      )}
    </div>
  )
}


function ContributionsTab() {
  const [subTab, setSubTab] = useState<ContribSubTab>('sync')

  return (
    <div>
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', padding: '0 0.5rem' }}>
        {(['sync', 'incoming'] as ContribSubTab[]).map((t) => (
          <button
            key={t}
            onClick={() => setSubTab(t)}
            style={{
              background: 'none', border: 'none', cursor: 'pointer',
              padding: '0.45rem 0.75rem', fontSize: '0.75rem', fontWeight: 600,
              color: subTab === t ? 'var(--amber)' : 'var(--text-dim)',
              borderBottom: subTab === t ? '2px solid var(--amber)' : '2px solid transparent',
              marginBottom: -1, transition: 'color 0.15s',
            }}
          >
            {t === 'sync' ? 'Sync status' : 'Incoming'}
          </button>
        ))}
      </div>
      <div key={subTab} style={{ animation: 'pageEnter 0.2s ease forwards' }}>
        {subTab === 'sync' && <SyncStatusView />}
        {subTab === 'incoming' && <IncomingContributionsView />}
      </div>
    </div>
  )
}

// ─── Main ─────────────────────────────────────────────────────────────────────

type AdminTab = 'review' | 'history' | 'export' | 'contributions'

export default function Admin() {
  const [unlocked, setUnlocked] = useState(!ADMIN_PASSWORD)
  const [activeTab, setActiveTab] = useState<AdminTab>('review')

  if (!unlocked) {
    return (
      <div className="page page-enter" style={{ display: 'flex', flexDirection: 'column' }}>
        <PasswordGate onUnlock={() => setUnlocked(true)} />
      </div>
    )
  }

  const tabs: Array<{ id: AdminTab; label: string }> = [
    { id: 'review', label: 'Review queue' },
    { id: 'history', label: 'History' },
    { id: 'export', label: 'Export' },
    { id: 'contributions', label: 'Contributions' },
  ]

  return (
    <div className="page page-enter" style={{ overflowY: 'auto' }}>
      <div style={{ maxWidth: 680, margin: '0 auto' }}>
        {/* Header */}
        <div style={{ padding: '1.25rem 1rem 0.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <h1 className="section-heading">Admin</h1>
          <span style={{ fontSize: '0.68rem', color: 'var(--text-dim)', fontWeight: 600 }}>
            ◎ Data quality
          </span>
        </div>

        {/* Tab bar */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', padding: '0 1rem' }}>
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                background: 'none', border: 'none', cursor: 'pointer',
                padding: '0.6rem 0.9rem', fontSize: '0.82rem', fontWeight: 600,
                color: activeTab === tab.id ? 'var(--amber)' : 'var(--text-dim)',
                borderBottom: activeTab === tab.id ? '2px solid var(--amber)' : '2px solid transparent',
                marginBottom: -1, transition: 'color 0.15s',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div key={activeTab} style={{ animation: 'pageEnter 0.2s ease forwards' }}>
          {activeTab === 'review' && <ReviewTab />}
          {activeTab === 'history' && <HistoryTab />}
          {activeTab === 'export' && <ExportTab />}
          {activeTab === 'contributions' && <ContributionsTab />}
        </div>
      </div>
    </div>
  )
}
