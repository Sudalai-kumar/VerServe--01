import { useEffect, useState } from 'react'
import axios from 'axios'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { HelpRequest } from './Feed'
import './MapView.css'
import '../components/HelpRequestCard.css' // Reuse trust styles
import { useMemo } from 'react'

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

// Fix leaflet default icon path issues with Vite
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

const API = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

const createIcon = (color: string) =>
  L.divIcon({
    html: `<div class="map-pin" style="background:${color};box-shadow:0 2px 8px ${color}66">
             <div class="map-pin-inner"></div>
           </div>`,
    className: '',
    iconSize: [32, 32],
    iconAnchor: [16, 32],
    popupAnchor: [0, -36],
  })

interface MapPinData {
  id: number
  title: string
  description: string
  location: string
  lat: number
  lng: number
  trust_score: number
  status: string
  trust_reasoning?: string
  category: string
  image_url?: string
  helper_count?: number
  people_needed?: number
}

const yellowIcon = createIcon('#F1C40F') // Seeking Help
const blueIcon   = createIcon('#3498DB') // Help Found
const greenIcon  = createIcon('#2ECC71') // Completed task
const redIcon    = createIcon('#E74C3C') // Flagged (Not shown but for completeness)

export default function MapView() {
  const [pins, setPins] = useState<MapPinData[]>([])
  const [category, setCategory] = useState('All')
  const [selected, setSelected] = useState<MapPinData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAll = async () => {
      setLoading(true)
      try {
        const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` }
        const res = await axios.get(`${API}/requests/`, { headers })
        const formatted: MapPinData[] = res.data.map((p: any) => ({
          ...p,
          location: p.location_name
        }))

        setPins(formatted)
      } catch (err) {
        console.error("Failed to fetch map data", err)
      } finally {
        setLoading(false)
      }
    }
    fetchAll()
  }, [])

  const getIcon = (pin: MapPinData) => {
    if (pin.status === 'seeking') return yellowIcon
    if (pin.status === 'help_found') return blueIcon
    if (pin.status === 'completed') return greenIcon
    return greenIcon
  }

  const filteredPins = useMemo(() => {
    let result = pins
    if (category !== 'All') {
      result = result.filter(p => p.category === category)
    }
    return result
  }, [pins, category])

  return (
    <div className="map-page page-content">
      <div className="page-container">
        <div className="section-header">
          <div>
            <h1 className="section-title">Mutual Aid Map 🗺️</h1>
            <p className="section-subtitle">
              Neighbor helping neighbor. Find someone nearby who needs a hand.
            </p>
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
          <div className="map-legend">
            <span className="legend-item"><span className="dot yellow" />Seeking Help</span>
            <span className="legend-item"><span className="dot blue" />Helping</span>
            <span className="legend-item"><span className="dot green" />Completed</span>
          </div>
        </div>

        <div className="map-layout">
          <div className="map-wrapper card">
            {loading ? (
              <div className="map-loading skeleton" />
            ) : (
              <MapContainer
                center={[13.0827, 80.2707]}
                zoom={12}
                className="leaflet-map"
                scrollWheelZoom={true}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://openstreetmap.org">OpenStreetMap</a>'
                />
                {filteredPins.map(pin => {
                  const jitterLat = (pin.lat ?? 13.0827) + (Math.random() - 0.5) * 0.001;
                  const jitterLng = (pin.lng ?? 80.2707) + (Math.random() - 0.5) * 0.001;
                  
                  return (
                    <Marker
                      key={`p2p-${pin.id}`}
                      position={[jitterLat, jitterLng]}
                      icon={getIcon(pin)}
                      eventHandlers={{ click: () => setSelected(pin) }}
                    >
                      <Popup className="map-popup-container">
                        <div className="map-popup">
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <p className="popup-ngo">🤝 {pin.category}</p>
                            <span className="pill pill-yellow" style={{ fontSize: '10px', padding: '1px 6px' }}>
                              P2P
                            </span>
                          </div>
                          <h4 className="popup-title">{pin.title}</h4>
                          <p className="popup-location">📍 {pin.location}</p>
                          <div className="trust-meter-p2p mini" style={{ margin: '4px 0' }}>
                             <span className="trust-score-p2p" style={{ 
                               color: pin.trust_score >= 80 ? 'var(--trust-green)' : pin.trust_score >= 50 ? 'var(--action-blue)' : '#e11d48',
                               fontSize: '0.75rem',
                               margin: 0
                             }}>
                               🛡️ {pin.trust_score}% Legit
                             </span>
                          </div>
                        </div>
                      </Popup>
                    </Marker>
                  );
                })}
              </MapContainer>
            )}
          </div>

          {selected && (
            <div className="map-sidebar card anim-fade-up">
              <button
                className="sidebar-close"
                onClick={() => setSelected(null)}
                aria-label="Close"
              >✕</button>
              
              <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                <span className="pill pill-yellow">NEIGHBOR HELP</span>
                <span className={`pill ${selected.status === 'completed' ? 'pill-green' : 'pill-yellow'}`}>
                  {selected.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
              
              {selected.image_url && (
                <div className="map-sidebar-image" style={{ margin: '0 0 16px', height: 160, overflow: 'hidden', borderRadius: 12, border: '1px solid var(--border)' }}>
                  <img src={selected.image_url.startsWith('http') ? selected.image_url : `${API}${selected.image_url}`} alt={selected.title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                </div>
              )}

              <p className="popup-ngo" style={{ color: 'var(--action-blue)' }}>Mutual Aid Request</p>
              <h3 className="popup-title" style={{ fontSize: '1.25rem', margin: '4px 0 12px', lineHeight: 1.2 }}>{selected.title}</h3>
              
              <div className="trust-meter-p2p" style={{ marginBottom: 20 }}>
                 <div className="trust-score-p2p" style={{ 
                   color: selected.trust_score >= 80 ? 'var(--trust-green)' : selected.trust_score >= 50 ? 'var(--action-blue)' : '#e11d48'
                 }}>
                   <span className="trust-icon">{selected.trust_score >= 80 ? '🛡️' : selected.trust_score >= 50 ? '🔍' : '⚠️'}</span>
                   <strong>{selected.trust_score}% Legitimacy Score</strong>
                 </div>
                 {selected.trust_reasoning && <p className="trust-reasoning-p2p">{selected.trust_reasoning}</p>}
              </div>

              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: 20 }}>
                {selected.description}
              </p>
              
              <div className="opp-info-row" style={{ marginTop: 14, background: 'var(--bg)', padding: '10px 14px', borderRadius: 8 }}>
                <span className="opp-info-item">📍 {selected.location}</span>
                {selected.helper_count !== undefined && (
                  <span className="opp-info-item">🤝 {selected.helper_count} / {selected.people_needed} Helpers</span>
                )}
              </div>
              
              <div className="map-sidebar-actions" style={{ marginTop: 24, display: 'flex', flexDirection: 'column', gap: 10 }}>
                <a 
                  href={`https://www.google.com/maps/dir/?api=1&destination=${selected.lat},${selected.lng}`}
                  target="_blank"
                  className="btn btn-primary"
                  style={{ width: '100%', justifyContent: 'center', padding: '12px' }}
                >
                  📍 Navigate to Task
                </a>
                <button 
                   className="btn btn-ghost"
                   style={{ width: '100%', justifyContent: 'center', padding: '12px' }}
                   onClick={() => window.location.href = '/feed'}
                >
                   View Details in Feed
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="map-count-bar">
          <span>🏘️ Found {filteredPins.length} requests matching your interest in Chennai</span>
        </div>
      </div>
    </div>
  )
}
