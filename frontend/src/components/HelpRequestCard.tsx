import { useState } from 'react'
import axios from 'axios'
import { useAuth } from '../context/AuthContext'
import { Link } from 'react-router-dom'
import ChatRoom from './ChatRoom'
import './HelpRequestCard.css'

import { API_URL as API } from '../config'

interface HelpRequestCardProps {
  req: {
    id: number
    user_id: number
    owner_name: string
    owner_karma: number
    title: string
    description: string
    helper_count: number
    people_needed: number
    category: string
    status: string
    is_joined: boolean
    join_status?: string
    location_name: string
    image_url?: string
    trust_score: number
    trust_reasoning?: string
    applications?: any[]
  }
  onUpdate: () => void
  style?: any
}

export default function HelpRequestCard({ req, onUpdate, style }: HelpRequestCardProps) {
  const { user } = useAuth()
  const isOwner = user?.id === req.user_id
  const [showChat, setShowChat] = useState(false)

  const handleJoin = async () => {
    try {
      await axios.post(`${API}/requests/${req.id}/join`, {}, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      onUpdate()
    } catch (err) {
      alert('Login to help')
    }
  }

  const handleAction = async (action: string, helperId?: number) => {
    try {
      const url = helperId 
        ? `${API}/requests/${req.id}/${action}/${helperId}`
        : action === 'cancel'
          ? `${API}/requests/${req.id}`
          : `${API}/requests/${req.id}/${action}`;
      
      const method = action === 'cancel' ? 'delete' : 'post';
      
      await axios({
        method,
        url,
        data: {},
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      
      onUpdate()
    } catch (err: any) {
      const msg = err.response?.data?.detail || `Error performing ${action}`;
      alert(msg);
    }
  }

  return (
    <div className={`help-card animate-in ${req.status}`} style={style}>
      <div className="help-card-header">
        <span className={`category-tag ${req.category.toLowerCase().replace(' ', '-')}`}>
          {req.category}
        </span>
        <span className={`status-badge ${req.status}`}>
          {req.status === 'seeking' ? 'Help Needed' : req.status === 'help_found' ? 'Helper Found' : 'Completed'}
        </span>
      </div>
      
      <div className="requester-info">
        <span className="requester-avatar">👤</span>
        <span className="requester-name">
          Posted by <Link to={`/profile/${req.user_id}`} className="profile-link"><strong>{req.owner_name}</strong></Link>
          {req.owner_karma > 100 && (
            <span className="trusted-neighbor-badge" title="Trusted Neighbor (> 100 Karma)">
              🛡️ Trusted
            </span>
          )}
        </span>
      </div>
      
      <div className="help-card-body">
        {req.image_url && (
          <div className="help-card-image">
            <img src={req.image_url.startsWith('http') ? req.image_url : `${API}${req.image_url}`} alt={req.title} />
          </div>
        )}
        <div className="trust-meter-p2p">
          <div className="trust-score-p2p" style={{ 
            color: req.trust_score >= 80 ? 'var(--trust-green)' : req.trust_score >= 50 ? 'var(--action-blue)' : '#e11d48'
          }}>
            <span className="trust-icon">{req.trust_score >= 80 ? '🛡️' : req.trust_score >= 50 ? '🔍' : '⚠️'}</span>
            <strong>{req.trust_score}% Legitimacy Score</strong>
          </div>
          {req.trust_reasoning && <p className="trust-reasoning-p2p">{req.trust_reasoning}</p>}
        </div>
        <h3 className="help-card-title">{req.title}</h3>
        <p className="help-card-desc">{req.description}</p>
        <div className="help-card-location">📍 {req.location_name}</div>
      </div>

      {/* Owner View: Manage Helpers */}
      {isOwner && req.applications && req.applications.length > 0 && (
        <div className="manage-helpers-section">
          <h4>Helpers</h4>
          <div className="helper-list">
            {req.applications.map(app => (
              <div key={app.user.id} className="helper-item">
                <div className="helper-item-info">
                  <span className="helper-name">{app.user.full_name || 'Neighbor'}</span>
                  <span className={`helper-status-tag ${app.status}`}>{app.status}</span>
                </div>
                <div className="helper-item-actions">
                  {app.status === 'requested' && (
                    <>
                      <button className="accept-btn-sm" onClick={() => handleAction('accept', app.user.id)}>Accept</button>
                      <button className="reject-btn-sm" onClick={() => handleAction('reject', app.user.id)}>Decline</button>
                    </>
                  )}
                  {app.status === 'confirmed' && (
                    <a 
                      href={`mailto:${app.user.email}`} 
                      className="contact-btn-sm" 
                      title="Open your email app to contact this neighbor"
                    >
                      Email 📧
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="help-card-footer">
        <div className="helper-count">
          <strong>{req.helper_count} / {req.people_needed}</strong> Confirmed
        </div>
        
        <div className="help-card-actions">
          <button 
            type="button"
            className={`chat-toggle-btn ${showChat ? 'active' : ''}`}
            onClick={() => setShowChat(!showChat)}
            title="Questions & Discussion"
          >
            💬 Discussion
          </button>

          {isOwner ? (
            req.status !== 'completed' && (
              <div className="owner-actions">
                {req.helper_count > 0 ? (
                  <button className="complete-btn" onClick={() => handleAction('complete')}>Complete Task ✨</button>
                ) : (
                  <button className="cancel-pill-btn" onClick={() => handleAction('cancel')} title="Delete this request">Cancel Request 🗑️</button>
                )}
              </div>
            )
          ) : (
            req.status !== 'completed' && (
              req.is_joined ? (
                <div className="status-group">
                   <span className={`join-status-pill ${req.join_status}`}>
                     {req.join_status === 'requested' ? '⏳ Requested' : '✅ Confirmed'}
                   </span>
                   <button className="leave-link" onClick={() => handleAction('leave')}>Cancel</button>
                </div>
              ) : (
                <button 
                  className="join-btn" 
                  onClick={handleJoin}
                  disabled={req.status === 'help_found'}
                >
                  {req.status === 'help_found' ? 'Mission Full' : 'Count me in! 🙋‍♂️'}
                </button>
              )
            )
          )}
        </div>
      </div>

      {showChat && <ChatRoom requestId={req.id} ownerId={req.user_id} />}
    </div>
  )
}
