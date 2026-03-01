import './TrustBadge.css'

interface TrustBadgeProps {
  score: number
  status: string
  showScore?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export default function TrustBadge({ score, status, showScore = true, size = 'md' }: TrustBadgeProps) {
  const getBadgeInfo = () => {
    if (status === 'verified' || score >= 90) {
      return { label: 'Verified', icon: '🛡️', cls: 'badge-green', bar: 'bar-green' }
    } else if (status === 'needs_review' || score >= 50) {
      return { label: 'Needs Review', icon: '🔍', cls: 'badge-yellow', bar: 'bar-yellow' }
    } else {
      return { label: 'Flagged', icon: '⚠️', cls: 'badge-red', bar: 'bar-red' }
    }
  }

  const { label, icon, cls, bar } = getBadgeInfo()

  return (
    <div className={`trust-badge ${cls} size-${size}`}>
      <span className="badge-icon">{icon}</span>
      <div className="badge-content">
        <span className="badge-label">{label}</span>
        {showScore && (
          <div className="badge-score-row">
            <div className="badge-bar">
              <div
                className={`badge-bar-fill ${bar}`}
                style={{ width: `${score}%` }}
              />
            </div>
            <span className="badge-num">{score}</span>
          </div>
        )}
      </div>
    </div>
  )
}
