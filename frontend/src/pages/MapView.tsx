import { useEffect, useState } from 'react'
import axios from 'axios'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import TrustBadge from '../components/TrustBadge'
import { Opportunity } from '../components/OpportunityCard'
import './MapView.css'

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

const greenIcon  = createIcon('#00A86B')
const yellowIcon = createIcon('#FFB830')

export default function MapView() {
  const [pins, setPins] = useState<Opportunity[]>([])
  const [selected, setSelected] = useState<Opportunity | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    axios.get(`${API}/opportunities/map-pins`)
      .then(r => setPins(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="map-page page-content">
      <div className="page-container">
        <div className="section-header">
          <div>
            <h1 className="section-title">Chennai Volunteer Map 🗺️</h1>
            <p className="section-subtitle">
              Colour-coded pins: 🟢 Verified · 🟡 Needs Review
            </p>
          </div>
          <div className="map-legend">
            <span className="legend-item"><span className="dot green" />Verified</span>
            <span className="legend-item"><span className="dot yellow" />Needs Review</span>
          </div>
        </div>

        <div className="map-layout">
          {/* Map */}
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
                {pins.map(pin => (
                  <Marker
                    key={pin.id}
                    position={[pin.lat ?? 13.0827, pin.lng ?? 80.2707]}
                    icon={pin.status === 'verified' ? greenIcon : yellowIcon}
                    eventHandlers={{ click: () => setSelected(pin) }}
                  >
                    <Popup className="map-popup-container">
                      <div className="map-popup">
                        <p className="popup-ngo">{pin.ngo_name}</p>
                        <h4 className="popup-title">{pin.title}</h4>
                        <TrustBadge score={pin.trust_score} status={pin.status} size="sm" />
                        <p className="popup-location">📍 {pin.location}</p>
                      </div>
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            )}
          </div>

          {/* Selected pin detail sidebar */}
          {selected && (
            <div className="map-sidebar card anim-fade-up">
              <button
                className="sidebar-close"
                onClick={() => setSelected(null)}
                aria-label="Close"
              >✕</button>
              <TrustBadge score={selected.trust_score} status={selected.status} size="sm" />
              <p className="popup-ngo" style={{ marginTop: 12 }}>{selected.ngo_name}</p>
              <h3 className="popup-title" style={{ fontSize: '1.1rem', margin: '6px 0 10px' }}>{selected.title}</h3>
              <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
                {selected.description}
              </p>
              <div className="opp-info-row" style={{ marginTop: 14 }}>
                <span className="opp-info-item">📍 {selected.location}</span>
                <span className="opp-info-item pill pill-blue">{selected.category}</span>
              </div>
              {selected.contact && (
                <a href={`tel:${selected.contact}`} className="btn btn-ghost" style={{ marginTop: 14, width: '100%', justifyContent: 'center' }}>
                  📞 Call NGO
                </a>
              )}
              {selected.source_url ? (
                <a
                  href={selected.source_url}
                  target="_blank"
                  rel="noreferrer"
                  className="btn btn-primary"
                  style={{ marginTop: 10, width: '100%', justifyContent: 'center' }}
                >
                  🙋 Volunteer Now
                </a>
              ) : (
                <button
                  className="btn btn-primary"
                  style={{ marginTop: 10, width: '100%', justifyContent: 'center' }}
                >
                  🙋 Volunteer Now
                </button>
              )}
            </div>
          )}
        </div>

        <div className="map-count-bar">
          <span>📌 Showing {pins.length} active opportunities across Chennai</span>
          {selected && (
            <span style={{ color: 'var(--trust-green)' }}>
              · Viewing: <strong>{selected.title}</strong>
            </span>
          )}
        </div>
      </div>
    </div>
  )
}
