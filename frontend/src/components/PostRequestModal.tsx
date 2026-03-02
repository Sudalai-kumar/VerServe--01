import { useState } from 'react'
import axios from 'axios'
import './PostRequestModal.css'

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'
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

interface PostRequestModalProps {
  onClose: () => void
  onSuccess: () => void
}

export default function PostRequestModal({ onClose, onSuccess }: PostRequestModalProps) {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'General',
    people_needed: 1,
    lat: 13.0827,
    lng: 80.2707,
    location_name: 'Chennai',
    image_url: '',
  })
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [loading, setLoading] = useState(false)
  const [locLoading, setLocLoading] = useState(false)

  const handleGetLocation = () => {
    setLocLoading(true)
    navigator.geolocation.getCurrentPosition((pos) => {
      setFormData({ ...formData, lat: pos.coords.latitude, lng: pos.coords.longitude, location_name: 'Current Location' })
      setLocLoading(false)
    }, () => {
      // Silent fallback to Chennai center if GPS fails
      setFormData({ ...formData, lat: 13.0827, lng: 80.2707, location_name: 'Chennai (Default)' })
      setLocLoading(false)
    })
  }
  
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      setImageFile(file)
      
      setUploading(true)
      const uploadData = new FormData()
      uploadData.append('file', file)
      
      try {
        const res = await axios.post(`${API}/uploads/`, uploadData, {
          headers: { 
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${localStorage.getItem('token')}` 
          }
        })
        setFormData(prev => ({ ...prev, image_url: res.data.url }))
      } catch (err) {
        alert('Failed to upload image')
      } finally {
        setUploading(false)
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await axios.post(`${API}/requests/`, formData, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      onSuccess()
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Error posting request. Please check if you are logged in.';
      alert(`Oops: ${msg}`);
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="modal-overlay">
      <div className="modal-card">
        <div className="modal-header">
          <h2>Post a Help Request 🤝</h2>
          <button className="close-btn" onClick={onClose}>&times;</button>
        </div>
        
        <form className="modal-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Title</label>
            <input 
              required
              placeholder="e.g. Need help moving a sofa"
              value={formData.title}
              onChange={e => setFormData({ ...formData, title: e.target.value })}
            />
          </div>
          
          <div className="form-group">
            <label>Category</label>
            <select 
              value={formData.category}
              onChange={e => setFormData({ ...formData, category: e.target.value })}
            >
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>

          <div className="form-group">
            <label>Description</label>
            <textarea 
              required
              rows={3}
              placeholder="Explain what exactly you need help with..."
              value={formData.description}
              onChange={e => setFormData({ ...formData, description: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label>Photo of Request (Mandatory for verification) 🖼️</label>
            <div className={`file-upload-zone ${formData.image_url ? 'has-file' : ''}`}>
              <input 
                type="file" 
                accept="image/*"
                onChange={handleFileChange}
                id="file-input"
                style={{ display: 'none' }}
              />
              <label htmlFor="file-input" className="file-label">
                {uploading ? 'Uploading...' : formData.image_url ? '✅ Photo Uploaded' : 'Click to upload or drag photo'}
              </label>
            </div>
            {formData.image_url && (
              <div className="upload-preview">
                <img src={formData.image_url.startsWith('http') ? formData.image_url : `${API}${formData.image_url}`} alt="Preview" />
              </div>
            )}
            <p className="form-hint" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              Providing an image helps neighbors trust your request.
            </p>
          </div>
          
          <div className="form-row">
            <div className="form-group col-half">
              <label>People Needed</label>
              <input 
                type="number" 
                min="1"
                max="10"
                value={formData.people_needed}
                onChange={e => setFormData({ ...formData, people_needed: parseInt(e.target.value) })}
              />
            </div>
            <div className="form-group col-half">
              <label>Location Map Pin</label>
              <button 
                type="button" 
                className="location-btn" 
                onClick={handleGetLocation}
                disabled={locLoading}
              >
                {locLoading ? 'Finding you...' : formData.location_name.includes('Default') ? 'Location: Chennai (Auto) 📍' : 'Pin Current Location 📍'}
              </button>
            </div>
          </div>

          <div className="modal-footer">
            <button type="button" className="cancel-btn" onClick={onClose}>Cancel</button>
            <button type="submit" className="submit-btn" disabled={loading || uploading || !formData.image_url}>
              {loading ? 'Posting...' : 'Post Request'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
