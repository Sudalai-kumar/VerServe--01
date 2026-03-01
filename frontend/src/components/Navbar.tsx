import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import './Navbar.css'

const NAV_LINKS = [
  { path: '/',         label: 'Feed',    icon: '📱' },
  { path: '/map',      label: 'Map',     icon: '🗺️' },
  { path: '/impact',   label: 'Impact',  icon: '📊' },
  { path: '/verify',   label: 'Verify',  icon: '🛡️' },
]

export default function Navbar() {
  const location = useLocation()
  const { user, logout } = useAuth()
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const closeMobileMenu = () => setMobileMenuOpen(false)

  return (
    <nav className="navbar">
      <div className="page-container navbar-inner">
        <Link to="/" className="navbar-logo" onClick={closeMobileMenu}>
          <div className="logo-icon">🦁</div>
          <span className="logo-text">VeriServe <span className="logo-accent">Chennai</span></span>
          <span className="logo-tag">Beta</span>
        </Link>

        <ul className="navbar-links">
          {NAV_LINKS.map(link => (
            <li key={link.path}>
              <Link
                to={link.path}
                className={`nav-link ${location.pathname === link.path ? 'active' : ''}`}
              >
                <span className="nav-emoji">{link.icon}</span>
                <span>{link.label}</span>
              </Link>
            </li>
          ))}
        </ul>

        <div className="nav-actions">
          {user ? (
            <div className="user-profile">
              <div className="user-info">
                <span className="user-name">{user.full_name || user.email.split('@')[0]}</span>
                <span className="user-role">{user.is_ngo_admin ? 'NGO Admin' : 'Volunteer'}</span>
              </div>
              <button onClick={logout} className="logout-btn" title="Logout">
                🚪
              </button>
            </div>
          ) : (
            <Link to="/login" className="login-btn" onClick={closeMobileMenu}>
              Login
            </Link>
          )}

          <button 
            className="hamburger" 
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? '✕' : '☰'}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="mobile-menu anim-fade-up">
          {NAV_LINKS.map(link => (
            <Link
              key={link.path}
              to={link.path}
              className={`mobile-link ${location.pathname === link.path ? 'active' : ''}`}
              onClick={closeMobileMenu}
            >
              <span className="nav-emoji">{link.icon}</span>
              <span>{link.label}</span>
            </Link>
          ))}
          {!user && (
            <Link to="/login" className="mobile-link" onClick={closeMobileMenu}>
              🔑 Login
            </Link>
          )}
        </div>
      )}
    </nav>
  )
}
