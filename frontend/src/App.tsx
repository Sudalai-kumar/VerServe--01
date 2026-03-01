import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Feed from './pages/Feed'
import MapView from './pages/MapView'
import MyImpact from './pages/MyImpact'
import VerifyCenter from './pages/VerifyCenter'
import NGODirectory from './pages/NGODirectory'
import AuthPage from './pages/AuthPage'
import './index.css'

function App() {
  return (
    <Router>
      <Navbar />
      <main>
        <Routes>
          <Route path="/"              element={<Feed />} />
          <Route path="/feed"          element={<Feed />} />
          <Route path="/map"           element={<MapView />} />
          <Route path="/impact"        element={<MyImpact />} />
          <Route path="/verify"        element={<VerifyCenter />} />
          <Route path="/ngo-directory" element={<NGODirectory />} />
          <Route path="/login"         element={<AuthPage />} />
        </Routes>
      </main>
    </Router>
  )
}

export default App
