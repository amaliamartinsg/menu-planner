# PyPlanner

Aplicación de gestión de recetas y menús semanales con cálculo automático de macronutrientes.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
pip install -r requirements.txt
cp .env.example .env        # Rellenar con las claves API reales
```

## Arrancar

```bash
# Terminal 1 — Backend
uvicorn app.backend.main:app --reload --port 8000

# Terminal 2 — Frontend
python frontend/main.py
```

Ver [planning/03_APIS_EXTERNAS.md](planning/03_APIS_EXTERNAS.md) para configurar las APIs externas.
