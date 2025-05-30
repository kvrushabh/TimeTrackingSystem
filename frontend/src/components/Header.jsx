import React from 'react'
import { AppBar, Toolbar, Typography, Button } from '@mui/material'
import { useAuth } from '../context/AuthContext.jsx'

const Header = () => {
  const { logout } = useAuth()
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Time Tracking System
        </Typography>
        <Button color="inherit" onClick={logout}>Logout</Button>
      </Toolbar>
    </AppBar>
  )
}

export default Header
