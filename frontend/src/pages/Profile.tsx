import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import axios from 'axios'
import './MyImpact.css' // Reuse the same premium styling

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface Badge { name: string; icon: string; description: string; earned: boolean }
interface ImpactData {
  user_id: number
  full_name: string
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

export default function Profile() {
  const { id } = useParams<{ id: string }>()
  const [data, setData] = useState<ImpactData | null>(null)
  const [history, setHistory] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  const fetchProfile = async () => {
    setLoading(true)
    setError(false)
    try {
      const [impactRes, historyRes] = await Promise.all([
        axios.get(`${API}/impact/${id}`),
        axios.get(`${API}/impact/history/${id}`) 
      ])
      setData(impactRes.data)
      setHistory(historyRes.data)
    } catch (err) {
      console.error('Failed to fetch profile', err)
      setError(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) {
      fetchProfile()
    }
  }, [id])

  if (loading) return (
    <div className="page-content"><div className="page-container">
      <div className="impact-skeleton">
        {[...Array(4)].map((_, i) => <div key={i} className="skeleton" style={{ height: 120, borderRadius: 16, marginBottom: 16 }} />)}
      </div>
    </div></div>
  )

  if (error || !data) return (
    <div className="page-content"><div className="page-container">
      <div className="empty-state">
        <div className="empty-state-icon">👤</div>
        <h3>Profile Not Found</h3>
        <p>This neighbor hasn't started their impact journey yet or the ID is invalid.</p>
        <Link to="/feed" className="btn btn-primary" style={{ marginTop: 20, textDecoration: 'none' }}>Back to Feed</Link>
      </div>
    </div></div>
  )

  return (
    <div className="page-content">
      <div className="page-container">
        <div className="impact-hero">
          <div className="impact-avatar">🦁</div>
          <div className="impact-hero-info">
            <p className="impact-user-label">
               Neighbor: <strong>{data.full_name}</strong>
            </p>
            <h1 className="impact-rank">{data.rank}</h1>
            <p className="impact-milestone">🎯 {data.next_milestone}</p>
          </div>
        </div>

        <div className="impact-stats grid-3">
          <div className="impact-stat-card card karma-special">
            <div className="stat-big purple">{data.karma}</div>
            <div className="stat-label">Neighbor Karma</div>
          </div>
          <div className="impact-stat-card card">
            <div className="stat-big green">{data.hours_volunteered}h</div>
            <div className="stat-label">Hours Volunteered</div>
          </div>
          <div className="impact-stat-card card">
            <div className="stat-big blue">{data.activities_count}</div>
            <div className="stat-label">Activities Done</div>
          </div>
        </div>

        <div style={{ marginTop: 40 }}>
          <h2 className="section-title">Community Expertise 🏅</h2>
          <div className="card" style={{ padding: 24, marginTop: 16 }}>
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
              <p style={{ color: 'var(--text-muted)' }}>No expertise data available yet.</p>
            )}
          </div>
        </div>

        <div style={{ marginTop: 40 }}>
          <h2 className="section-title">Activity History 📜</h2>
          {history.length > 0 ? (
            <div className="history-feed" style={{ marginTop: 16 }}>
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
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)', marginTop: 16 }}>
              <p>No activity history found for this neighbor.</p>
            </div>
          )}
        </div>

        <div style={{ marginTop: 40 }}>
           <h2 className="section-title">Badges Earned</h2>
           <div className="badges-grid" style={{ marginTop: 16 }}>
            {data.badges.filter(b => b.earned).map(badge => (
              <div key={badge.name} className="badge-card card earned">
                <div className="badge-emoji">{badge.icon}</div>
                <h4 className="badge-name">{badge.name}</h4>
                <p className="badge-desc">{badge.description}</p>
                <span className="pill pill-green earned-pill">✓ Earned</span>
              </div>
            ))}
            {data.badges.filter(b => b.earned).length === 0 && (
                <p style={{ color: 'var(--text-muted)' }}>No badges earned yet.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
