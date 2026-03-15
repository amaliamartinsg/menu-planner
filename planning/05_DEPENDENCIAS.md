# 📦 05 — Dependencias y Setup del Entorno

---

## requirements.txt

```txt
# ─────────────────────────────────────────
# BACKEND — FastAPI + SQLModel
# ─────────────────────────────────────────
fastapi>=0.111.0           # Framework web async
uvicorn[standard]>=0.29.0  # Servidor ASGI con recarga automática
sqlmodel>=0.0.18           # ORM que unifica SQLAlchemy + Pydantic
pydantic>=2.7.0            # Validación de datos (incluida en FastAPI)
pydantic-settings>=2.2.0   # Gestión de variables de entorno (.env)
python-dotenv>=1.0.0       # Carga el archivo .env

# ─────────────────────────────────────────
# INTEGRACIONES EXTERNAS
# ─────────────────────────────────────────
httpx>=0.27.0              # Cliente HTTP async (USDA, Unsplash)
openai>=1.30.0             # SDK oficial OpenAI (GPT-4o mini)

# ─────────────────────────────────────────
# FRONTEND — Flet
# ─────────────────────────────────────────
flet>=0.22.0               # UI framework Python (Material Design 3)

# ─────────────────────────────────────────
# UTILIDADES
# ─────────────────────────────────────────
python-dateutil>=2.9.0     # Manipulación de fechas (semanas del menú)

# ─────────────────────────────────────────
# DESARROLLO Y TESTING (opcional)
# ─────────────────────────────────────────
pytest>=8.0.0              # Testing del core/
pytest-asyncio>=0.23.0     # Tests async
httpx                      # También usado para TestClient de FastAPI
```

---

## Setup Inicial (paso a paso)

### 1. Clonar / crear el proyecto

```bash
mkdir recipe-manager
cd recipe-manager
git init
```

### 2. Entorno virtual

```bash
# Crear
python -m venv .venv

# Activar (Mac/Linux)
source .venv/bin/activate

# Activar (Windows CMD)
.venv\Scripts\activate.bat

# Activar (Windows PowerShell)
.venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con las claves API reales
```

### 5. Arrancar el backend

```bash
# Desde la raíz del proyecto
uvicorn app.backend.main:app --reload --port 8000

# Verificar en el navegador:
# http://localhost:8000/docs  → Swagger UI
# http://localhost:8000/redoc → ReDoc
```

### 6. Arrancar el frontend (nueva terminal)

```bash
# Activar .venv también en esta terminal
source .venv/bin/activate

# Desde la raíz del proyecto
python app/frontend/main.py
```

---

## Estructura del `.gitignore`

```gitignore
# Entorno virtual
.venv/
venv/
env/

# Variables de entorno (NUNCA subir al repo)
.env

# Base de datos SQLite
*.db
*.db-journal

# Python
__pycache__/
*.py[cod]
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/

# IDEs
.vscode/settings.json
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
```

---

## Herramientas Recomendadas

### VS Code Extensions
| Extensión | Para qué |
|---|---|
| **Python** (Microsoft) | IntelliSense, linting, debugging |
| **Pylance** | Type checking mejorado |
| **Markdown Preview Enhanced** | Ver este plan con checkboxes interactivos |
| **Todo Tree** | Ver todos los `- [ ]` pendientes en el sidebar |
| **SQLite Viewer** | Inspeccionar la BD SQLite directamente |
| **REST Client** | Testear endpoints sin Swagger (archivos `.http`) |
| **GitLens** | Control de versiones mejorado |

### Instalación rápida de extensiones VS Code

```bash
code --install-extension ms-python.python
code --install-extension ms-python.pylance
code --install-extension shd101wyy.markdown-preview-enhanced
code --install-extension Gruntfuggly.todo-tree
code --install-extension qwtel.sqlite-viewer
```

### Herramientas externas
- **DB Browser for SQLite**: Aplicación de escritorio para inspeccionar la BD — [sqlitebrowser.org](https://sqlitebrowser.org)

---

## Comandos Útiles de Desarrollo

```bash
# Reiniciar la BD (útil durante desarrollo)
rm recipe_manager.db && python app/data/seed.py

# Ejecutar tests del core
pytest app/core/tests/ -v

# Formatear código
black app/

# Verificar tipos
mypy app/backend/ app/core/

# Ver logs del backend con más detalle
uvicorn app.backend.main:app --reload --log-level debug

# Generar requirements.txt actualizado
pip freeze > requirements.txt
```

---

## Variables de Entorno — Referencia Completa

| Variable | Requerida | Descripción |
|---|---|---|
| `USDA_API_KEY` | ✅ Sí | Clave de USDA FoodData Central |
| `UNSPLASH_ACCESS_KEY` | ✅ Sí | Access key de Unsplash |
| `OPENAI_API_KEY` | ✅ Sí | Clave de OpenAI |
| `BACKEND_URL` | ⚠️ Opcional | URL del backend (default: `http://localhost:8000`) |
| `DATABASE_URL` | ⚠️ Opcional | URL de la BD (default: `sqlite:///./recipe_manager.db`) |

---

## Diagrama de Procesos (Arranque)

```
Terminal 1:                          Terminal 2:
─────────────────────────────────    ─────────────────────────────────
$ source .venv/bin/activate          $ source .venv/bin/activate
$ uvicorn app.backend.main:app       $ python app/frontend/main.py
  --reload --port 8000

  FastAPI server running             Flet app opens window
  → localhost:8000                   → makes HTTP calls to
  → SQLite DB created/connected        localhost:8000
  → All tables created
```
