/**
 * Centralized API configuration.
 * Auto-detects production vs local environment using the hostname.
 * This avoids relying on Docker build-args or runtime env vars.
 */
const isLocal =
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1'

export const API_URL = isLocal
  ? (import.meta.env.VITE_API_URL ?? 'http://localhost:8000')
  : 'https://goodneighbor-api.azurewebsites.net'
