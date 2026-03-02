import { useEffect, useState } from 'react'
import axios from 'axios'
import { useAuth } from '../context/AuthContext'
import './MyImpact.css'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface Badge { name: string; icon: string; description: string; earned: boolean }
interface ImpactData {
  user_id: number
  hours_volunteered: number
  activities_count: number
  verifications_count: number
  karma: number
  badges: Badge[]
  rank: string
  next_milestone: string
  category_stats: string
}

interface Activity {
  id: number
  type: string
  category: string
  hours: number
  image_url: string | null
  created_at: string
}

export default function MyImpact() {
  const { user, loading: authLoading } = useAuth()
  const [data, setData] = useState<ImpactData | null>(null)
  const [history, setHistory] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const [showKarmaGuide, setShowKarmaGuide] = useState(false)

  const CATEGORIES = [
    'General', 
    'Environment',
    'Education',
    'Health',
    'Elderly Care',
    'Disaster Relief',
    'Food & Nutrition',
    'Women Empowerment',
    'Home Helper', 
    'Grocery Run', 
    'Pet Care', 
    'Tech Support', 
    'Events', 
  ]

  const fetchImpact = async () => {
    if (!user) return
    setLoading(true)
    setError(false)
    try {
      const [impactRes, historyRes] = await Promise.all([
        axios.get(`${API}/impact/me`),
        axios.get(`${API}/impact/history`)
      ])
      setData(impactRes.data)
      setHistory(historyRes.data)
    } catch (err) {
      console.error('Failed to fetch impact', err)
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!authLoading && user) {
      fetchImpact()
    } else if (!authLoading && !user) {
      setLoading(false)
    }
  }, [user, authLoading])

  // Toast logic removed with manual logging

  // Manual logging removed to ensure Karma integrity (P2P Verified only)

  if (authLoading || loading) return (
    <div className="page-content"><div className="page-container">
      <div className="impact-skeleton">
        {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: 120, borderRadius: 16, marginBottom: 16 }} />)}
      </div>
    </div></div>
  )

  if (!user) return (
    <div className="page-content"><div className="page-container">
      <div className="empty-state">
        <div className="empty-state-icon">🔒</div>
        <h3>Authentication Required</h3>
        <p>Login to track your impact and earn badges in Chennai.</p>
        <a href="/login" className="btn btn-primary" style={{ marginTop: 20, textDecoration: 'none' }}>Go to Login</a>
      </div>
    </div></div>
  )

  if (error || !data) return (
    <div className="page-content"><div className="page-container">
      <div className="empty-state">
        <div className="empty-state-icon">⚠️</div>
        <h3>Failed to load impact</h3>
        <p>There was an error fetching your data. Please try again later.</p>
        <button className="btn btn-primary" style={{ marginTop: 20 }} onClick={fetchImpact}>Retry</button>
      </div>
    </div></div>
  )

  const hoursPercent = Math.min((data.hours_volunteered / 50) * 100, 100)

  return (
    <div className="page-content">
      <div className="page-container">
        {/* Toasts removed */}

        <div className="impact-hero">
          <div className="impact-avatar">🦁</div>
          <div className="impact-hero-info">
            <p className="impact-user-label">
              👤 {user.full_name || user.email}
            </p>
            <h1 className="impact-rank">{data.rank}</h1>
            <p className="impact-milestone">🎯 {data.next_milestone}</p>
          </div>
        </div>

        <div className="impact-stats grid-4">
          <div className="impact-stat-card card karma-special" onClick={() => setShowKarmaGuide(!showKarmaGuide)} style={{ cursor: 'pointer' }}>
            <div className="stat-big purple">{data.karma}</div>
            <div className="stat-label">Neighbor Karma</div>
            <div className="stat-sublabel">How it works? <span className="click-hint">Click to see</span> 🤝</div>
          </div>
          <div className="impact-stat-card card">
            <div className="stat-big green">{data.hours_volunteered}h</div>
            <div className="stat-label">Hours Volunteered</div>
            <div className="progress-bar" style={{ marginTop: 10 }}>
              <div className="progress-fill" style={{ width: `${hoursPercent}%`, background: 'var(--trust-green)' }} />
            </div>
          </div>
          <div className="impact-stat-card card">
            <div className="stat-big blue">{data.activities_count}</div>
            <div className="stat-label">Activities Done</div>
          </div>
          {/* Verifications removed for P2P model */}
        </div>

        {showKarmaGuide && (
          <div className="karma-guide animate-in card" style={{ marginTop: 24, padding: 32 }}>
            <div className="guide-header">
              <h3>🤝 How to earn Neighbor Karma?</h3>
              <button className="btn-close" onClick={() => setShowKarmaGuide(false)}>✕</button>
            </div>
            <div className="guide-grid grid-2" style={{ marginTop: 20 }}>
              <div className="guide-item">
                <span className="guide-pts">+30</span>
                <div className="guide-text">
                  <strong>Provide Help</strong>
                  <p>Earned when you are a confirmed helper on a completed task.</p>
                </div>
              </div>
              <div className="guide-item" style={{ gridColumn: 'span 2', background: 'rgba(59, 130, 246, 0.05)', marginTop: 10 }}>
                <span className="guide-pts">💡</span>
                <div className="guide-text">
                  <strong>Pure Giving</strong>
                  <p>In P2P mode, Karma represents your *contribution* to Chennai. You don't earn points for receiving help or posting.</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Manual Log Your Activity removed - Karma integrity hardening */}

        <div style={{ marginTop: 40 }}>
          <div className="section-header">
            <div>
              <h2 className="section-title">Community Expertise 🏅</h2>
              <p className="section-subtitle">Your helpfulness breakdown by neighborhood category</p>
            </div>
          </div>
          <div className="card" style={{ padding: 24 }}>
            {Object.keys(JSON.parse(data.category_stats || '{}')).length > 0 ? (
              <div className="expertise-grid">
                {Object.entries(JSON.parse(data.category_stats || '{}')).map(([cat, count]) => (
                  <div key={cat} className="expertise-item">
                    <div className="expertise-info">
                      <span className="expertise-name">{cat}</span>
                      <span className="expertise-count">{count as number} { (count as number) === 1 ? 'Task' : 'Tasks' }</span>
                    </div>
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ 
                          width: `${Math.min(((count as number) / 10) * 100, 100)}%`, 
                          background: 'linear-gradient(90deg, var(--action-blue) 0%, var(--trust-green) 100%)' 
                        }} 
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state" style={{ padding: '20px 0' }}>
                <p>Complete your first neighbhorly task to unlock expertise stats!</p>
              </div>
            )}
          </div>
        </div>

        <div style={{ marginTop: 40 }}>
          <div className="section-header">
            <div>
              <h2 className="section-title">Activity History 📜</h2>
              <p className="section-subtitle">Your log of community contributions</p>
            </div>
          </div>
          {history.length > 0 ? (
            <div className="history-feed">
              {history.map(activity => (
                <div key={activity.id} className="history-item card anim-fade-up">
                  <div className="history-content">
                    <div className="history-main">
                      <div className="history-type-icon">{activity.type === 'activity' ? '🕒' : '✅'}</div>
                      <div>
                        <div className="history-title">
                          {activity.type === 'activity' ? `Completed ${activity.hours}h task` : 'Verified a community post'}
                        </div>
                        <div className="history-meta">
                          <span className="pill pill-blue">{activity.category}</span>
                          <span className="history-date">{new Date(activity.created_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                    </div>
                    {activity.image_url && (
                      <div className="history-proof" onClick={() => window.open(`${API}${activity.image_url}`, '_blank')}>
                         <img src={`${API}${activity.image_url}`} alt="Proof" />
                         <div className="proof-overlay">🔍 View Proof</div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
              <p>No activity history found. Start helping today!</p>
            </div>
          )}
        </div>

        <div style={{ marginTop: 40 }}>
          <div className="section-header">
            <div>
              <h2 className="section-title">Your Badges</h2>
              <p className="section-subtitle">
                {data.badges.filter(b => b.earned).length} of {data.badges.length} earned
              </p>
            </div>
          </div>
          <div className="badges-grid">
            {data.badges.map(badge => (
              <div key={badge.name} className={`badge-card card${badge.earned ? ' earned' : ' locked'}`}>
                <div className="badge-emoji">{badge.icon}</div>
                <h4 className="badge-name">{badge.name}</h4>
                <p className="badge-desc">{badge.description}</p>
                {badge.earned
                  ? <span className="pill pill-green earned-pill">✓ Earned</span>
                  : <span className="pill locked-pill">🔒 Locked</span>
                }
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
