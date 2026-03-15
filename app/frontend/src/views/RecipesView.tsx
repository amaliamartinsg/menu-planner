import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'

function RecipesView() {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" fontWeight={600} gutterBottom>
        Recetas
      </Typography>
      <Typography color="text.secondary">En construcción</Typography>
    </Box>
  )
}

export default RecipesView
