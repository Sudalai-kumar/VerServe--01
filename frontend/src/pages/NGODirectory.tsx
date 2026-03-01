import { useEffect, useState, useMemo } from 'react'
import axios from 'axios'
import './NGODirectory.css'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface NGO {
  id: number; name: string; description: string; category: string
  contact_email?: string; contact_phone?: string; website?: string
  address?: string; logo_emoji: string; founded_year?: number
  volunteers_count: number; verified: boolean
}

export default function NGODirectory() {
  const [ngos, setNgos] = useState<NGO[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [error, setError] = useState(false)

  useEffect(() => {
    axios.get(`${API}/ngos/`)
      .then(r => setNgos(r.data))
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [])

  // Memoize filtered NGOs (case-insensitive)
  const filtered = useMemo(() => {
    const term = search.toLowerCase()
    return ngos.filter(n =>
      n.name.toLowerCase().includes(term) ||
      n.category.toLowerCase().includes(term)
    )
  }, [ngos, search])

  return (
    <div className="page-content">
      <div className="page-container">
        {/* Header */}
        <div className="ngo-hero">
          <div>
            <h1 className="section-title">NGO Directory 🏢</h1>
            <p className="section-subtitle">
              Pre-vetted, registered organisations you can trust. All are verified by VeriServe.
            </p>
          </div>
          <input
            className="ngo-search"
            type="text"
            placeholder="🔍 Search NGOs or categories..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        {/* Grid */}
        {loading ? (
          <div className="ngo-grid">
            {[...Array(6)].map((_, i) => <div key={i} className="skeleton" style={{ height: 280, borderRadius: 20 }} />)}
          </div>
        ) : error ? (
          <div className="empty-state">
            <div className="empty-state-icon">⚠️</div>
            <h3>Backend not connected</h3>
            <p>Start the FastAPI server at port 8000 to load the NGO directory.</p>
            <div className="error-hint"><code>cd backend &amp;&amp; uvicorn main:app --reload</code></div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🔍</div>
            <h3>No NGOs found</h3>
            <p>Try a different search term.</p>
          </div>
        ) : (
          <div className="ngo-grid">
            {filtered.map((ngo, i) => (
              <div key={ngo.id} className="ngo-card card anim-fade-up" style={{ animationDelay: `${i * 60}ms` }}>
                {/* Top */}
                <div className="ngo-card-top">
                  <div className="ngo-logo">{ngo.logo_emoji}</div>
                  <div className="ngo-header-info">
                    <div className="ngo-verified-row">
                      <span className="pill pill-green ngo-verified-pill">🛡️ Verified</span>
                      <span className="pill pill-blue">{ngo.category}</span>
                    </div>
                    <h3 className="ngo-name">{ngo.name}</h3>
                  </div>
                </div>

                {/* Body */}
                <p className="ngo-desc">{ngo.description}</p>

                {/* Stats */}
                <div className="ngo-stats-row">
                  {ngo.founded_year && (
                    <div className="ngo-stat">
                      <span className="ngo-stat-val">{ngo.founded_year}</span>
                      <span className="ngo-stat-label">Founded</span>
                    </div>
                  )}
                  <div className="ngo-stat">
                    <span className="ngo-stat-val">{ngo.volunteers_count.toLocaleString('en-IN')}+</span>
                    <span className="ngo-stat-label">Volunteers</span>
                  </div>
                </div>

                {/* Footer */}
                <div className="ngo-card-footer">
                  {ngo.address && <p className="ngo-address">📍 {ngo.address}</p>}
                  <div className="ngo-links">
                    {ngo.contact_phone && (
                      <a href={`tel:${ngo.contact_phone}`} className="btn btn-ghost ngo-btn">📞 Call</a>
                    )}
                    {ngo.website && (
                      <a href={ngo.website} target="_blank" rel="noreferrer" className="btn btn-primary ngo-btn">
                        🌐 Website
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
