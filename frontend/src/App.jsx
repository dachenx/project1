import { Navigate, Route, Routes } from 'react-router-dom'
import Chat from './pages/Chat'
import KBManage from './pages/KBManage'
import Login from './pages/Login'

function PrivateRoute({ children }) {
  const token = localStorage.getItem('token')
  return token ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Chat />
          </PrivateRoute>
        }
      />
      <Route
        path="/kb"
        element={
          <PrivateRoute>
            <KBManage />
          </PrivateRoute>
        }
      />
    </Routes>
  )
}
