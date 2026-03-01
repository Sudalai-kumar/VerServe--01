import { useState, useEffect, useMemo } from 'react'
import axios from 'axios'
import OpportunityCard, { Opportunity } from '../components/OpportunityCard'
import './Feed.css'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const FILTERS = [
  { key: 'all',          label: 'All',           emoji: '🌐' },
  { key: 'verified',     label: 'Verified ✅',   emoji: '' },
  { key: 'needs_review', label: 'Needs Review 🔍',emoji: '' },
]

export default function Feed() {
  const [opps, setOpps] = useState<Opportunity[]>([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  // Fetch ALL once on mount
  useEffect(() => {
    setLoading(true)
    setError(false)
    axios.get(`${API}/opportunities/`)
      .then(r => setOpps(r.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [])

  // Memoize filtered list
  const filteredOpps = useMemo(() => {
    if (filter === 'all') return opps
    return opps.filter(o => o.status === filter)
  }, [opps, filter])

  // Memoize stats
  const stats = useMemo(() => {
    return {
      verified: opps.filter(o => o.status === 'verified').length,
      review:   opps.filter(o => o.status === 'needs_review').length,
      total:    opps.length
    }
  }, [opps])

  return (
    <div className="page-content">
      <div className="page-container">
        {/* Hero */}
        <div className="feed-hero">
          <div className="feed-hero-text">
            <h1 className="feed-hero-title">
              Chennai's <span className="hero-highlight">Verified</span> Volunteer Feed
            </h1>
            <p className="feed-hero-sub">
              Real-time volunteering opportunities, filtered through the Trust Engine.
              Only safe, verified opportunities reach this feed.
            </p>
          </div>
          {/* Stats row */}
          <div className="feed-stats">
            <div className="stat-card">
              <div className="stat-num green">{stats.verified}</div>
              <div className="stat-label">Verified</div>
            </div>
            <div className="stat-card">
              <div className="stat-num yellow">{stats.review}</div>
              <div className="stat-label">Needs Review</div>
            </div>
            <div className="stat-card">
              <div className="stat-num blue">{stats.total}</div>
              <div className="stat-label">Total Active</div>
            </div>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="section-header">
          <div>
            <h2 className="section-title">Opportunities</h2>
            <p className="section-subtitle">Updated live via the VeriServe Trust Engine</p>
          </div>
          <div className="filter-tabs">
            {FILTERS.map(f => (
              <button
                key={f.key}
                className={`filter-tab${filter === f.key ? (f.key === 'verified' ? ' active-green' : ' active') : ''}`}
                onClick={() => setFilter(f.key)}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="feed-grid">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="skeleton-card skeleton" />
            ))}
          </div>
        ) : error ? (
          <div className="empty-state">
            <div className="empty-state-icon">⚠️</div>
            <h3>Backend not connected</h3>
            <p>Start the FastAPI server at port 8000 to load live data.</p>
            <div className="error-hint">
              <code>cd backend && uvicorn main:app --reload</code>
            </div>
          </div>
        ) : filteredOpps.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🔍</div>
            <h3>No opportunities found</h3>
            <p>Try switching the filter or run the seeder to populate data.</p>
          </div>
        ) : (
          <div className="feed-grid">
            {filteredOpps.map((opp, i) => (
              <OpportunityCard
                key={opp.id}
                opp={opp}
                style={{ animationDelay: `${i * 60}ms` }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
