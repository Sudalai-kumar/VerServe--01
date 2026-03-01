import { MapPin, Phone, ExternalLink, Clock } from 'lucide-react'
import TrustBadge from './TrustBadge'
import './OpportunityCard.css'

export interface Opportunity {
  id: number
  title: string
  description: string
  ngo_name: string
  location: string
  trust_score: number
  status: string
  trust_reasoning?: string
  category: string
  contact?: string
  source: string
  source_url?: string
  created_at?: string
  lat?: number
  lng?: number
}

interface Props {
  opp: Opportunity
  onVerify?: (id: number, action: 'confirm' | 'flag') => void
  showVerifyActions?: boolean
  style?: React.CSSProperties
}

const CATEGORY_COLORS: Record<string, string> = {
  'Environment':        '#00A86B',
  'Education':          '#1E90FF',
  'Health':             '#9B5CF6',
  'Disaster Relief':    '#FF6B35',
  'Elder Care':         '#F59E0B',
  'Food & Nutrition':   '#EF4444',
  'Women Empowerment':  '#EC4899',
  'Civic & Environment':'#14B8A6',
  'General':            '#6B7280',
}

export default function OpportunityCard({ opp, onVerify, showVerifyActions = false, style }: Props) {
  const catColor = CATEGORY_COLORS[opp.category] || '#6B7280'
  const timeAgo = opp.created_at
    ? new Date(opp.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
    : 'Recently'

  return (
    <div className="opp-card card anim-fade-up" style={style}>
      {/* Header strip */}
      <div className="opp-card-header" style={{ borderColor: catColor + '33' }}>
        <div className="opp-card-meta">
          <span className="opp-category pill" style={{ background: catColor + '18', color: catColor }}>
            {opp.category}
          </span>
          <span className="opp-source pill pill-blue">
            {opp.source === 'rss' ? '📡 RSS' : '📱 Social'}
          </span>
        </div>
        <TrustBadge score={opp.trust_score} status={opp.status} size="sm" />
      </div>

      <div className="opp-card-body">
        {/* NGO & Title */}
        <p className="opp-ngo">{opp.ngo_name}</p>
        <h3 className="opp-title">{opp.title}</h3>
        <p className="opp-description">{opp.description.slice(0, 120)}{opp.description.length > 120 ? '…' : ''}</p>

        {/* AI Insight / Reasoning */}
        {opp.trust_reasoning && (
          <div className="opp-ai-insight">
            <span className="ai-icon">🤖</span>
            <p className="ai-reason">{opp.trust_reasoning}</p>
          </div>
        )}

        {/* Info row */}
        <div className="opp-info-row">
          <span className="opp-info-item">
            <MapPin size={13} />
            {opp.location}
          </span>
          <span className="opp-info-item">
            <Clock size={13} />
            {timeAgo}
          </span>
        </div>
      </div>

      {/* Actions */}
      <div className="opp-card-footer">
        {showVerifyActions && onVerify ? (
          <div className="verify-actions">
            <button
              className="btn btn-success"
              onClick={() => onVerify(opp.id, 'confirm')}
            >
              ✓ Confirm
            </button>
            <button
              className="btn btn-danger"
              onClick={() => onVerify(opp.id, 'flag')}
            >
              ✗ Flag
            </button>
          </div>
        ) : (
          <>
            {opp.contact && (
              <a href={`tel:${opp.contact}`} className="btn btn-ghost opp-contact">
                <Phone size={14} />
                Contact
              </a>
            )}
            {opp.source_url ? (
              <a
                href={opp.source_url}
                target="_blank"
                rel="noreferrer"
                className="btn btn-primary opp-volunteer-btn"
              >
                <ExternalLink size={14} />
                Volunteer Now
              </a>
            ) : (
              <button className="btn btn-primary opp-volunteer-btn">
                <ExternalLink size={14} />
                Volunteer Now
              </button>
            )}
          </>
        )}
      </div>
    </div>
  )
}
