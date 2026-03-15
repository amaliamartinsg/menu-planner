import { useState, useEffect } from 'react'
import { Routes, Route, useLocation, useNavigate } from 'react-router-dom'
import Box from '@mui/material/Box'
import BottomNavigation from '@mui/material/BottomNavigation'
import BottomNavigationAction from '@mui/material/BottomNavigationAction'
import Paper from '@mui/material/Paper'
import RestaurantMenuIcon from '@mui/icons-material/RestaurantMenu'
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth'
import SettingsIcon from '@mui/icons-material/Settings'
import RecipesView from './views/RecipesView'
import MenuView from './views/MenuView'
import SettingsView from './views/SettingsView'

const ROUTES = ['/', '/menu', '/settings']

function App() {
  const location = useLocation()
  const navigate = useNavigate()
  const [tabValue, setTabValue] = useState(0)

  useEffect(() => {
    const idx = ROUTES.indexOf(location.pathname)
    if (idx !== -1) setTabValue(idx)
  }, [location.pathname])

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
    navigate(ROUTES[newValue])
  }

  return (
    <Box sx={{ pb: 7 }}>
      <Routes>
        <Route path="/" element={<RecipesView />} />
        <Route path="/menu" element={<MenuView />} />
        <Route path="/settings" element={<SettingsView />} />
      </Routes>

      <Paper
        sx={{ position: 'fixed', bottom: 0, left: 0, right: 0 }}
        elevation={3}
      >
        <BottomNavigation value={tabValue} onChange={handleTabChange}>
          <BottomNavigationAction
            label="Recetas"
            icon={<RestaurantMenuIcon />}
          />
          <BottomNavigationAction
            label="Menú"
            icon={<CalendarMonthIcon />}
          />
          <BottomNavigationAction
            label="Ajustes"
            icon={<SettingsIcon />}
          />
        </BottomNavigation>
      </Paper>
    </Box>
  )
}

export default App
