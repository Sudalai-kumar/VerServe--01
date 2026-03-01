import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { useAuth } from '../context/AuthContext'
import './AuthPage.css'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [isNgoAdmin, setIsNgoAdmin] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      if (isLogin) {
        const params = new URLSearchParams()
        params.append('username', email)
        params.append('password', password)
        
        const res = await axios.post(`${API}/auth/token`, params)
        await login(res.data.access_token)
        navigate('/')
      } else {
        await axios.post(`${API}/auth/signup`, {
          email,
          password,
          full_name: fullName,
          is_ngo_admin: isNgoAdmin,
        })
        setIsLogin(true)
        setError('Account created! Please login.')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-logo">🦁</div>
          <h1>{isLogin ? 'Welcome Back' : 'Join VeriServe'}</h1>
          <p>{isLogin ? 'Login to access Chennai\'s verified feed' : 'Protect your city, track your impact'}</p>
        </div>

        <form className="auth-form" onSubmit={handleSubmit}>
          {!isLogin && (
            <>
              <div className="form-group">
                <label>Full Name</label>
                <input 
                  type="text" 
                  placeholder="John Doe" 
                  value={fullName}
                  onChange={e => setFullName(e.target.value)}
                  required
                />
              </div>
              <div className="form-group-row">
                <input 
                  type="checkbox" 
                  id="ngo-admin"
                  checked={isNgoAdmin}
                  onChange={e => setIsNgoAdmin(e.target.checked)}
                />
                <label htmlFor="ngo-admin">I am an NGO Representative</label>
              </div>
            </>
          )}
          
          <div className="form-group">
            <label>Email Address</label>
            <input 
              type="email" 
              placeholder="you@example.com" 
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label>Password</label>
            <input 
              type="password" 
              placeholder="••••••••" 
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </div>

          {error && <div className="auth-error">{error}</div>}

          <button type="submit" className="auth-submit" disabled={loading}>
            {loading ? 'Processing...' : (isLogin ? 'Login' : 'Sign Up')}
          </button>
        </form>

        <div className="auth-footer">
          <button onClick={() => setIsLogin(!isLogin)} className="auth-toggle">
            {isLogin ? "Don't have an account? Sign Up" : "Already have an account? Login"}
          </button>
        </div>
      </div>
    </div>
  )
}
