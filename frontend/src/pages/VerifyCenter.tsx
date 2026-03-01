import { useEffect, useState } from 'react'
import axios from 'axios'
import { useAuth } from '../context/AuthContext'
import OpportunityCard, { Opportunity } from '../components/OpportunityCard'
import './VerifyCenter.css'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export default function VerifyCenter() {
  const { user } = useAuth()
  const [queue, setQueue] = useState<Opportunity[]>([])
  const [loading, setLoading] = useState(true)
  const [toast, setToast] = useState<string | null>(null)

  useEffect(() => {
    axios.get(`${API}/opportunities/review-queue`)
      .then(r => setQueue(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 3000)
  }

  const handleVerify = async (id: number, action: 'confirm' | 'flag') => {
    try {
      const res = await axios.patch(`${API}/opportunities/${id}/verify`, { action })
      setQueue(prev => {
        const updated = prev.map(o => o.id === id ? res.data : o)
        // Remove from queue if no longer needs_review
        return updated.filter(o => o.status === 'needs_review')
      })
      showToast(action === 'confirm' ? '✅ Opportunity confirmed! Trust score increased.' : '🚩 Post flagged. Trust score lowered.')
    } catch (err: any) {
      if (err.response?.status === 401) {
        showToast('🔒 Please login to verify opportunities.')
      } else {
        showToast('❌ Action failed. Is the backend running?')
      }
    }
  }

  return (
    <div className="page-content">
      <div className="page-container">
        {/* Toast */}
        {toast && <div className="verify-toast">{toast}</div>}

        {/* Header */}
        <div className="verify-hero">
          <div>
            <h1 className="section-title">Verify Center ✅</h1>
            <p className="section-subtitle">
              Help the community! Review new posts and confirm or flag them.
              Your votes directly affect the Trust Score.
            </p>
          </div>
          <div className="verify-count-badge">
            <span className="verify-count">{queue.length}</span>
            <span className="verify-count-label">Awaiting Review</span>
          </div>
        </div>

        {/* How it works */}
        <div className="alert-banner info" style={{ marginBottom: 24 }}>
          ℹ️ <strong>How it works:</strong> Click <strong>Confirm</strong> if the opportunity looks legitimate. Click <strong>Flag</strong> if it seems suspicious. Posts crossing 90 points become Verified; those dropping below 50 are hidden.
        </div>

        {/* Queue */}
        {loading ? (
          <div className="feed-grid">
            {[...Array(4)].map((_, i) => <div key={i} className="skeleton-card skeleton" />)}
          </div>
        ) : queue.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🎉</div>
            <h3>Queue is clear!</h3>
            <p>All current posts have been reviewed. Check back later.</p>
          </div>
        ) : (
          <div className="feed-grid">
            {queue.map((opp, i) => (
              <OpportunityCard
                key={opp.id}
                opp={opp}
                showVerifyActions
                onVerify={handleVerify}
                style={{ animationDelay: `${i * 60}ms` }}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
