import { useEffect, useState, useRef } from 'react'
import axios from 'axios'
import { useAuth } from '../context/AuthContext'
import './ChatRoom.css'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface Message {
  id: number
  request_id: number
  user_id: number
  content: string
  created_at: string
  full_name: string
}

interface ChatRoomProps {
  requestId: number
  ownerId: number
}

export default function ChatRoom({ requestId, ownerId }: ChatRoomProps) {
  const { user } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [newMsg, setNewMsg] = useState('')
  const [sending, setSending] = useState(false)
  const chatEndRef = useRef<HTMLDivElement>(null)

  const fetchMessages = async () => {
    try {
      const res = await axios.get(`${API}/chat/${requestId}`)
      setMessages(res.data)
    } catch (err) {
      console.error('Failed to fetch chat', err)
    }
  }

  useEffect(() => {
    fetchMessages()
    // Poll for new messages every 5 seconds for "pseudo-realtime" feel
    const interval = setInterval(fetchMessages, 5000)
    return () => clearInterval(interval)
  }, [requestId])

  const isInitialLoad = useRef(true)

  useEffect(() => {
    if (isInitialLoad.current && messages.length > 0) {
      chatEndRef.current?.scrollIntoView({ behavior: 'auto' })
      isInitialLoad.current = false
    }
  }, [messages])

  // Only scroll to bottom when sending a message
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMsg.trim() || !user) return

    setSending(true)
    try {
      const token = localStorage.getItem('token')
      await axios.post(`${API}/chat/${requestId}`, 
        { content: newMsg },
        { headers: { Authorization: `Bearer ${token}` } }
      )
      setNewMsg('')
      await fetchMessages()
      scrollToBottom()
    } catch (err) {
      console.error('Failed to send message', err)
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="chat-room">
      <div className="chat-header">
        <h4>💬 Community Q&A</h4>
        <p>Ask anything about this request</p>
      </div>

      <div className="chat-messages">
        {messages.length === 0 ? (
          <div className="chat-empty">
            <p>No questions yet. Be the first to ask!</p>
          </div>
        ) : (
          messages.map(m => (
            <div key={m.id} className={`chat-bubble-container ${user?.id === m.user_id ? 'mine' : ''}`}>
              <div className="chat-bubble">
                <div className="chat-bubble-meta">
                  <span className="chat-user">
                    {m.full_name}
                    {m.user_id === ownerId && <span className="chat-author-tag"> (Author)</span>}
                  </span>
                  <span className="chat-time">{new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
                <div className="chat-content">{m.content}</div>
              </div>
            </div>
          ))
        )}
        <div ref={chatEndRef} />
      </div>

      <form className="chat-input-area" onSubmit={handleSend}>
        <input 
          type="text" 
          placeholder={user ? "Type your question..." : "Login to join the chat"}
          value={newMsg}
          onChange={e => setNewMsg(e.target.value)}
          disabled={!user || sending}
        />
        <button type="submit" className="btn-send" disabled={!user || !newMsg.trim() || sending}>
          {sending ? '...' : '✈️'}
        </button>
      </form>
      {!user && <p className="chat-login-hint">Please <a href="/login">login</a> to ask questions.</p>}
    </div>
  )
}
