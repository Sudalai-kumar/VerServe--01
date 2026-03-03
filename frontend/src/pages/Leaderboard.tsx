import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import axios from 'axios'
import './Leaderboard.css'

import { API_URL as API } from '../config'

interface LeaderboardEntry {
  rank: number
  user_id: number
  full_name: string
  karma: number
  activities_count: number
  hours_volunteered: number
  rank_title: string
}

export default function Leaderboard() {
  const [data, setData] = useState<LeaderboardEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get(`${API}/impact/leaderboard`)
      .then(r => setData(r.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="page-content center">Loading Leaderboard...</div>

  return (
    <div className="page-content">
      <div className="page-container">
        <div className="leaderboard-header">
          <div className="header-icon">🏆</div>
          <h1 className="header-title">Chennai Neighbor Leaderboard</h1>
          <p className="header-subtitle">Recognizing the most helpful souls in our city.</p>
        </div>

        <div className="leaderboard-card card animate-in">
          <table className="leaderboard-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Neighbor</th>
                <th>Credibility Title</th>
                <th className="text-right">Karma Points</th>
              </tr>
            </thead>
            <tbody>
              {data.map((entry) => (
                <tr key={entry.user_id} className={entry.rank <= 3 ? `top-rank rank-${entry.rank}` : ''}>
                  <td>
                    <span className="rank-badge">{entry.rank}</span>
                  </td>
                  <td>
                    <div className="neighbor-info">
                       <Link to={`/profile/${entry.user_id}`} className="neighbor-link">
                         <span className="neighbor-name">{entry.full_name}</span>
                       </Link>
                       <span className="neighbor-stats">{entry.activities_count} activities · {entry.hours_volunteered}h</span>
                    </div>
                  </td>
                  <td>
                    <span className="neighbor-rank-title">{entry.rank_title}</span>
                  </td>
                  <td className="text-right">
                    <span className="karma-count">{entry.karma}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {data.length === 0 && (
            <div className="empty-state" style={{ padding: '60px 0' }}>
               <div className="empty-state-icon">🏙️</div>
               <h3>The city is just starting to help.</h3>
               <p>Complete a help request to be the first on the board!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
