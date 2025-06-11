import React, { useState } from 'react';
import {
  AppBar, Toolbar, Typography, Button,
  Menu, MenuItem, IconButton
} from '@mui/material';
import AccountCircle from '@mui/icons-material/AccountCircle';
import { useAuth } from '../context/AuthContext.jsx';
import { useLocation } from 'react-router-dom';

const Header = () => {
  const { logout } = useAuth();
  const location = useLocation();
  const [anchorEl, setAnchorEl] = useState(null);

  // Get user from localStorage
  const user = JSON.parse(localStorage.getItem('user'));

  // Check if on login page
  const isLoginPage = location.pathname === '/login';

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    handleMenuClose();
    logout();
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          Time Tracking System
        </Typography>

        {user?.name && !isLoginPage && (
          <>
            <IconButton
              size="large"
              edge="end"
              color="inherit"
              onClick={handleMenuOpen}
            >
              <AccountCircle />
              <Typography sx={{ ml: 1 }}>{user.name}({user.role})</Typography>
            </IconButton>
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
            >
              <MenuItem onClick={handleLogout}>Logout</MenuItem>
            </Menu>
          </>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Header;
