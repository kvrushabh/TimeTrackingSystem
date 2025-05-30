import React from 'react'
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom'
import LoginPage from './pages/LoginPage.jsx'
import TaskListPage from './pages/TaskListPage.jsx'
import { AuthProvider, useAuth } from './context/AuthContext.jsx'
import Header from './components/Header.jsx'

const PrivateRoute = ({ children }) => {
  const { user } = useAuth()
  return user ? children : <Navigate to="/login" />
}

const App = () => (
  <AuthProvider>
    <Router>
      <Header />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/tasks" element={
          <PrivateRoute>
            <TaskListPage />
          </PrivateRoute>
        } />
        <Route path="*" element={<Navigate to="/tasks" />} />
      </Routes>
    </Router>
  </AuthProvider>
)

export default App
