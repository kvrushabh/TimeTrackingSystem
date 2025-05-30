import React, { useState } from 'react'
import { Box, Paper, Typography, TextField, Button } from '@mui/material'
import { useNavigate } from 'react-router-dom'

const LoginPage = () => {
  const navigate = useNavigate()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const handleLogin = (e) => {
    e.preventDefault()

    // You can replace this with actual API call
    if (username === 'admin' && password === 'admin') {
      console.log('Login successful')
      navigate('/task-listing')
    } else {
      alert('Invalid credentials')
    }
  }

  return (
    <Box
      sx={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
    >
      <Paper sx={{ padding: 4, width: 300 }}>
        <form onSubmit={handleLogin}>
          <Typography variant="h6" mb={2}>Login</Typography>
          <TextField
            label="Username"
            fullWidth
            margin="normal"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <TextField
            label="Password"
            type="password"
            fullWidth
            margin="normal"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 2 }}
          >
            Login
          </Button>
        </form>
      </Paper>
    </Box>
  )
}

export default LoginPage
