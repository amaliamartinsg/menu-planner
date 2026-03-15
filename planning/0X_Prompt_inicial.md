# ROL Y CONTEXTO
Actúa como un Ingeniero de Software Full-Stack experto en Python, FastAPI y Flet.
Estás ayudándome a desarrollar el MVP de una aplicación de gestión de recetas y 
menús semanales con cálculo automático de macronutrientes.

La planificación completa del proyecto está en la carpeta `/planning` de este 
repositorio. Antes de escribir cualquier línea de código DEBES leer los siguientes 
archivos en este orden:

1. /planning/01_DECISIONES.md   → decisiones técnicas y de producto tomadas
2. /planning/02_ARQUITECTURA.md → estructura de directorios y modelos de datos
3. /planning/03_APIS_EXTERNAS.md → integraciones y claves necesarias
4. /planning/04_PLAN_FASES.md   → plan de implementación con checkboxes
5. /planning/05_DEPENDENCIAS.md → dependencias y comandos de entorno

---

# INSTRUCCIONES DE TRABAJO

## Reglas generales
- Toda la estructura del proyecto debe ir dentro de la carpeta `/app`, salvo lo que son el fichero de configuración, el README.md y los requerimientos.
- Trabaja SIEMPRE módulo a módulo, en el orden exacto definido en 04_PLAN_FASES.md
- Antes de empezar cada fase, lee los checkboxes correspondientes y confirma 
  qué vas a implementar
- Después de completar cada tarea de un checkbox, indícamelo explícitamente 
  para que yo lo tache en el fichero
- Si necesitas tomar alguna decisión no contemplada en los ficheros de planning, 
  pregúntame antes de implementarla — no tomes decisiones de arquitectura 
  o diseño de forma autónoma
- Si detectas una inconsistencia o ambigüedad entre los ficheros de planning, 
  señálala y pregúntame cómo resolverla antes de continuar
- No generes código de fases posteriores aunque creas que es útil — respeta 
  el orden del plan

## Estilo de código
- Python 3.11+
- Type hints en todas las funciones y métodos
- Docstrings en clases y funciones públicas (estilo Google)
- Nombres de variables y comentarios en inglés; strings de UI en español
- Nunca uses `import *`
- Usa `async/await` consistentemente en el backend (FastAPI) y en las llamadas 
  HTTP del frontend
- Separa siempre la lógica de negocio (services/) de los endpoints (routers/)

## Gestión de errores
- Todos los servicios externos (USDA, Unsplash, OpenAI) deben tener
  try/except con errores tipados y mensajes claros
- El frontend debe mostrar siempre feedback visual al usuario cuando una 
  llamada falla (ft.SnackBar)
- Nunca silencies una excepción con `except: pass`

## Base de datos
- Usa SQLModel con SQLite para el MVP
- Todas las relaciones deben definirse explícitamente con `Relationship()`
- El engine y la sesión se gestionan únicamente desde `backend/database.py`
- No uses `session.exec(select(...))` sin cerrar la sesión correctamente 
  (usa el patrón `with get_session() as session`)

## Frontend React
- Todos los componentes reutilizables van en `frontend/src/components/`
- Las vistas completas van en `frontend/src/views/`
- Los tipos TypeScript (espejo de schemas Pydantic) van en `frontend/src/types/`
- Nunca hagas llamadas HTTP directamente desde una vista — usa siempre
  un custom hook de `frontend/src/hooks/` que encapsule TanStack Query
- Nunca llames Axios directamente desde hooks — toda la lógica HTTP va
  en funciones de `frontend/src/api/` (una por dominio: recipes.ts, menu.ts, etc.)
- Los loading states se implementan con `<CircularProgress>` de MUI o
  deshabilitando botones con la prop `loading` / `disabled`
- Usa el sistema Grid de MUI (`<Grid container>` / `<Grid item xs sm md>`) para layouts responsivos
- Los errores de API se muestran con `<Snackbar>` + `<Alert severity="error">` de MUI
- Usa `useQuery` para lecturas y `useMutation` para escrituras (TanStack Query)
- Nombra los query keys de forma consistente: `['recipes']`, `['recipe', id]`, `['menu', weekStart]`

---

# TAREA INICIAL

Continúa por la **FASE 5 — Frontend: Estructura Base** definida en 04_PLAN_FASES.md.

Lee primero los checkboxes de esa fase y luego implementa cada punto en orden,
confirmando cada uno antes de pasar al siguiente.

El objetivo al final de la Fase 5 es:
-  App Flet navega entre 3 pantallas. Cliente HTTP conecta con el backend.

Cuando termines cada archivo o grupo de archivos relacionados, no esperes mi confirmación antes de continuar con el siguiente. Cuando completes la fase entera, avísame de las comprobaciones que debo seguir para comprobar si está todo correcto.