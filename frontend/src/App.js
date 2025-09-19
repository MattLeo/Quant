import React from 'react';
import { 
  Container, 
  AppBar, 
  Toolbar, 
  Typography,
  Button,
  Box,
  CssBaseline,
  ThemeProvider,
  createTheme
} from '@mui/material';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import {
  Dashboard as DashboardIcon,
  Settings as SettingsIcon,
  TrendingUp as TradingIcon,
} from '@mui/icons-material';
import Dashboard from './components/Dashboard';
import ConfigPage from './components/ConfigPage';
import './App.css';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    success: {
      main: '#2e7d32',
    },
    error: {
      main: '#d32f2f',
    },
  },
});

function NavigationBar() {
  const location = useLocation();
  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <AppBar position='static' elevation={2}>
      <Toolbar>
        <TradingIcon sx={{mr: 2}} />
        <Typography variant='h6' component="div" sx={{flexGrow: 1}}>
          Algorithmic Trading System
        </Typography>

        <Box sx={{display: 'flex', gap: 1}}>
          <Button
            component={Link}
            to="/"
            color='inherit'
            startIcon={<DashboardIcon />}
            variant={isActive('/') ? 'outlined' : 'text' }
            sx={{
              borderColor: isActive('/') ? 'white' : 'transparent',
              backgroundColor: isActive('/') ? 'rgba(255, 255, 255, 0.1)' : 'transparent'
            }}
          > Dashboard</Button>

          <Button
            component={Link}
            to="/config"
            color='inherit'
            startIcon={<SettingsIcon />}
            variant={isActive('/config') ? 'outlined' : 'text'}
            sx={{
              borderColor: isActive('/config') ? 'white' : 'transparent',
              backgroundColor: isActive('/config') ? 'rgba(255, 255, 255, 0.1)' : 'transparent'
            }}
          >Configuration</Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}


function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{flexgrow: 1}}>
          <NavigationBar />
          <Container maxWidth='xl' sx={{mt: 3, mb: 4}}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/config" element={<ConfigPage />} />
            </Routes>
          </Container>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;