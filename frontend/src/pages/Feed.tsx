import { useState, useEffect, useMemo } from 'react'
import axios from 'axios'
import HelpRequestCard from '../components/HelpRequestCard'
import PostRequestModal from '../components/PostRequestModal'
import './Feed.css'

import { API_URL as API } from '../config'

export interface HelpRequest {
  id: number
  user_id: number
  owner_name: string
  owner_karma: number
  title: string
  description: string
  image_url?: string
  location_name: string
  lat: number
  lng: number
  people_needed: number
  helper_count: number
  category: string
  status: string
  created_at: string
  is_joined: boolean
  trust_score: number
  trust_reasoning?: string
  join_status?: string
}

const CATEGORIES = [
  'General', 
  'Home Helper', 
  'Elderly Care', 
  'Grocery Run', 
  'Pet Care', 
  'Gardening', 
  'Tech Support', 
  'Unloading', 
  'Events', 
  'Other'
]

export default function Feed() {
  const [requests, setRequests] = useState<HelpRequest[]>([])
  const [category, setCategory] = useState('All')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [showModal, setShowModal] = useState(false)

  const fetchRequests = () => {
    const token = localStorage.getItem('token')
    if (!token) {
      setLoading(false)
      return
    }

    setLoading(true)
    setError(false)
    axios.get(`${API}/requests/`, {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(r => setRequests(r.data))
      .catch((err) => {
        console.error('Feed fetch error:', err)
        setError(true)
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    fetchRequests()
  }, [])

  const filteredRequests = useMemo(() => {
    if (category === 'All') return requests
    return requests.filter(r => r.category === category)
  }, [requests, category])

  return (
    <div className="page-content">
      <div className="page-container">
        {/* Hero */}
        <div className="feed-hero">
          <div className="feed-hero-text">
            <h1 className="feed-hero-title">
              Hyper-local <span className="hero-highlight">Mutual Aid</span> Chennai
            </h1>
            <p className="feed-hero-sub">
              Need a hand? Post a request. Want to help? Browse the map and feed for neighbors nearby.
            </p>
            <button className="post-btn-hero" onClick={() => setShowModal(true)}>
              Post Help Request 🤝
            </button>
          </div>
          {/* Stats Simplified */}
          <div className="feed-stats-p2p">
            <div className="stat-card">
              <div className="stat-num blue">{requests.length}</div>
              <div className="stat-label">Active Requests</div>
            </div>
            <div className="stat-card">
              <div className="stat-num green">{requests.filter(r => r.helper_count > 0).length}</div>
              <div className="stat-label">Requests Helped</div>
            </div>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="section-header">
          <div>
            <h2 className="section-title">Nearby Help Requests</h2>
            <p className="section-subtitle">Real-time neighbor-to-neighbor requests</p>
          </div>
          <div className="filter-tabs">
            {['All', ...CATEGORIES].map(c => (
              <button
                key={c}
                className={`filter-tab${category === c ? ' active' : ''}`}
                onClick={() => setCategory(c)}
              >
                {c}
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
            <div className="empty-state-icon">🔒</div>
            <h3>Authentication Required</h3>
            <p>Please login to view and post help requests.</p>
          </div>
        ) : filteredRequests.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon">🏘️</div>
            <h3>No requests in your area</h3>
            <p>Be the first to ask for help or check back later.</p>
          </div>
        ) : (
          <div className="feed-grid">
            {filteredRequests.map((req, i) => (
              <HelpRequestCard
                key={req.id}
                req={req}
                onUpdate={fetchRequests}
                style={{ animationDelay: `${i * 60}ms` }}
              />
            ))}
          </div>
        )}
      </div>

      {showModal && (
        <PostRequestModal 
          onClose={() => setShowModal(false)} 
          onSuccess={() => {
            setShowModal(false);
            fetchRequests();
          }}
        />
      )}
    </div>
  )
}
