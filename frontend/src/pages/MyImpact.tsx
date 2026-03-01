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
  badges: Badge[]
  rank: string
  next_milestone: string
}

export default function MyImpact() {
  const { user, loading: authLoading } = useAuth()
  const [data, setData] = useState<ImpactData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  // Log-hours form state
  const [logType, setLogType] = useState<'activity' | 'verification'>('activity')
  const [logHours, setLogHours] = useState('')
  const [logging, setLogging] = useState(false)
  const [logToast, setLogToast] = useState<string | null>(null)

  const fetchImpact = async () => {
    if (!user) return
    setLoading(true)
    setError(false)
    try {
      const res = await axios.get(`${API}/impact/me`)
      setData(res.data)
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

  const showToast = (msg: string) => {
    setLogToast(msg)
    setTimeout(() => setLogToast(null), 3000)
  }

  const handleLog = async () => {
    if (!user) return
    setLogging(true)
    try {
      const hours = logType === 'activity' ? parseFloat(logHours) || 0 : 0
      await axios.post(`${API}/impact/log`, { type: logType, hours })
      await fetchImpact()
      setLogHours('')
      showToast(logType === 'activity' ? `✅ Logged ${hours}h activity!` : '✅ Verification logged!')
    } catch {
      showToast('❌ Failed to log. Are you logged in?')
    } finally {
      setLogging(false)
    }
  }

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
        {logToast && <div className="verify-toast">{logToast}</div>}

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

        <div className="impact-stats grid-3">
          <div className="impact-stat-card card">
            <div className="stat-big green">{data.hours_volunteered}h</div>
            <div className="stat-label">Hours Volunteered</div>
            <div className="progress-bar" style={{ marginTop: 10 }}>
              <div className="progress-fill" style={{ width: `${hoursPercent}%`, background: 'var(--trust-green)' }} />
            </div>
            <div className="stat-sublabel">{hoursPercent.toFixed(0)}% to Community Champion</div>
          </div>
          <div className="impact-stat-card card">
            <div className="stat-big blue">{data.activities_count}</div>
            <div className="stat-label">Activities Completed</div>
          </div>
          <div className="impact-stat-card card">
            <div className="stat-big yellow">{data.verifications_count}</div>
            <div className="stat-label">Posts Verified</div>
          </div>
        </div>

        <div className="card" style={{ marginTop: 32, padding: '24px 28px' }}>
          <h2 className="section-title" style={{ marginBottom: 16 }}>Log Your Activity</h2>
          <div className="log-form-row">
            <div className="filter-tabs">
              <button
                className={`filter-tab${logType === 'activity' ? ' active' : ''}`}
                onClick={() => setLogType('activity')}
              >🕒 Activity</button>
              <button
                className={`filter-tab${logType === 'verification' ? ' active' : ''}`}
                onClick={() => setLogType('verification')}
              >✅ Verification</button>
            </div>
            {logType === 'activity' && (
              <input
                className="user-edit-input"
                type="number"
                min="0"
                step="0.5"
                placeholder="Hours"
                value={logHours}
                onChange={e => setLogHours(e.target.value)}
                style={{ width: 160 }}
              />
            )}
            <button
              className="btn btn-primary"
              onClick={handleLog}
              disabled={logging || (logType === 'activity' && !logHours)}
            >
              {logging ? 'Logging…' : '+ Log'}
            </button>
          </div>
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
