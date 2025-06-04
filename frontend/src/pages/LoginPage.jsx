import React, { useState } from 'react'
import { Box, Button, Paper, TextField, Typography, Alert } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import api from '../api/axios'
import { useAuth } from '../context/AuthContext'

const LoginPage = () => {
  const navigate = useNavigate()
  const { login } = useAuth()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  console.log(username);
  console.log(password);
  console.log('---------------------');
  


  const handleLogin = async (e) => {
    e.preventDefault()
    try {
      const res = await api.post('/auth/login', { username, password })
      login({
        ...res.data.user,
        token: res.data.access_token,
      })
      navigate('/task')
    } catch (err) {
      console.error(err)
      setError(err.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <Box sx={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <Paper sx={{ padding: 4, width: 300 }}>
        <form onSubmit={handleLogin}>
          <Typography variant="h6" mb={2}>Login</Typography>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <TextField fullWidth label="Username" value={username} onChange={e => setUsername(e.target.value)} margin="normal" />
          <TextField fullWidth label="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} margin="normal" />
          <Button fullWidth variant="contained" type="submit" sx={{ mt: 2 }}>Login</Button>
        </form>
      </Paper>
    </Box>
  )
}

export default LoginPage
