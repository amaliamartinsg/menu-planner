# 🚀 04 — Plan de Implementación por Fases

> Tacha cada tarea cuando esté completada cambiando `[ ]` por `[x]`
> Las fases deben completarse en orden — cada una tiene dependencias de la anterior.

---

## Progreso Global

```
FASE 0  [██████████] 100% Setup
FASE 1  [██████████] 100% Modelos BD
FASE 2  [██████████] 100% Backend Recetas
FASE 3  [██████████] 100% Backend Menú
FASE 4  [██████████] 100% Backend Perfil
FASE 5  [          ] 0%   Frontend Base
FASE 6  [          ] 0%   Frontend Recetas
FASE 7  [          ] 0%   Frontend Menú
FASE 8  [          ] 0%   Frontend Ajustes
FASE 9  [          ] 0%   Polish & Testing
```

---

## FASE 0 — Setup y Scaffolding

> **Objetivo:** Proyecto arranca. Backend responde en localhost:8000. Frontend lanza ventana vacía.  
> **Dependencias:** Ninguna  
> **Duración estimada:** 1 sesión

- [x] Crear estructura de directorios completa (ver `02_ARQUITECTURA.md`)
- [x] Crear entorno virtual: `python -m venv .venv`
- [x] Activar entorno: `source .venv/bin/activate` (Linux/Mac) o `.venv\Scripts\activate` (Windows)
- [x] Instalar dependencias: `pip install -r requirements.txt`
- [x] Crear `.env` a partir de `.env.example` (en la raíz, fuera de `/app`)
- [x] Crear `app/backend/database.py` con engine SQLite y función `get_session()`
- [x] Crear `app/backend/main.py` con FastAPI, CORS habilitado para Flet (`localhost:*`)
- [x] Verificar que `uvicorn app.backend.main:app --reload` arranca sin errores
- [x] Verificar que `http://localhost:8000/docs` muestra Swagger UI
- [x] Crear `app/frontend/main.py` con Flet app mínima (ventana vacía con título)
- [x] Verificar que `python app/frontend/main.py` abre la ventana
- [x] Crear `app/frontend/api_client.py` con clase `APIClient` base (método `get` y `post` con httpx)
- [x] Crear `.gitignore` con: `.env`, `.venv/`, `__pycache__/`, `*.db`, `.DS_Store`
- [x] Commit inicial: `git init` + `git add .` + `git commit -m "feat: project scaffolding"`

---

## FASE 1 — Modelos y Base de Datos

> **Objetivo:** Todas las tablas existen en SQLite. El seed carga datos iniciales.  
> **Dependencias:** FASE 0 completa  
> **Duración estimada:** 1 sesión

### Modelos SQLModel
- [x] Crear `app/backend/models/category.py` — `Category`, `SubCategory`
- [x] Crear `app/backend/models/recipe.py` — `Recipe`, `RecipeIngredient`
- [x] Crear `app/backend/models/menu.py` — `MenuWeek`, `MenuDay`, `MenuSlot` + Enum `SlotType`
- [x] Crear `app/backend/models/extra.py` — `Extra`, `MenuDayExtra`
- [x] Crear `app/backend/models/profile.py` — `Profile` + Enums `ActivityLevel`, `Goal`
- [x] Crear `app/backend/models/__init__.py` exportando todos los modelos
- [x] Añadir `SQLModel.metadata.create_all(engine)` en `database.py`
- [x] Verificar creación de tablas ejecutando el backend (revisar con DB Browser for SQLite)

### Schemas Pydantic
- [x] Crear `app/backend/schemas/recipe.py` — `RecipeCreate`, `RecipeRead`, `RecipeUpdate`, `IngredientInput`
- [x] Crear `app/backend/schemas/menu.py` — `MenuWeekRead`, `SlotUpdate`, `DayMacrosSummary`
- [x] Crear `app/backend/schemas/category.py` — `CategoryCreate`, `CategoryRead` (con subcategorías anidadas)
- [x] Crear `app/backend/schemas/extra.py` — `ExtraCreate`, `ExtraRead`
- [x] Crear `app/backend/schemas/profile.py` — `ProfileUpdate`, `ProfileRead`

### Seed de datos iniciales
- [x] Crear `app/data/seed.py`
- [x] Seed: categorías por defecto (Desayuno, Comida, Cena, Snack con subcategorías)
- [x] Seed: perfil por defecto (id=1, valores razonables)
- [x] Seed: 3-5 extras predefinidos de ejemplo ("Café con leche", "Fruta", "Whey")
- [x] Seed: 2-3 recetas de ejemplo con ingredientes (para testear la UI)
- [x] Verificar ejecutando `python app/data/seed.py` y revisando la BD

---

## FASE 2 — Backend: CRUD de Recetas

> **Objetivo:** Todos los endpoints de recetas funcionan y son testeable en Swagger.  
> **Dependencias:** FASE 1 completa + claves API configuradas en `.env`  
> **Duración estimada:** 1-2 sesiones

### Servicios de integración
- [x] Crear `app/backend/services/usda.py`
  - [x] Función `get_nutrition(ingredient_name: str, quantity_g: float) -> NutritionResult`
  - [x] Traducción automática del nombre a inglés con GPT-4o mini antes de consultar USDA
  - [x] Caché en memoria `_translation_cache` para no repetir traducciones idénticas
  - [x] Fallback a `NutritionResult` con todos 0 si ingrediente no encontrado
  - [x] Conversión de respuesta al formato interno (kcal, prot_g, hc_g, fat_g)
  - [x] Error 403 si `USDA_API_KEY` es inválida; 502 para otros errores de red
- [x] Crear `app/backend/services/unsplash.py`
  - [x] Función `search_images(query: str, count: int = 5) -> list[str]`
  - [x] Error 403 si `UNSPLASH_ACCESS_KEY` es inválida (HTTP 401 de Unsplash → 403)
- [x] Crear `app/backend/services/openai_service.py`
  - [x] Función `suggest_recipe(ingredients: list[str]) -> RecipeSuggestion`
  - [x] Prompt estructurado que devuelve JSON (ver `03_APIS_EXTERNAS.md`)
  - [x] Validación del JSON devuelto con Pydantic
  - [x] Reintento con `temperature=0` si el JSON es inválido
  - [x] Error 403 si `OPENAI_API_KEY` es inválida
- [x] Crear `app/backend/services/macro_calculator.py`
  - [x] Función `calculate_recipe_macros(ingredients: list[RecipeIngredient]) -> MacroTotals`
  - [x] Fórmula: `(quantity_g / 100) * macro_100g` por cada ingrediente → sumar

### Router de recetas
- [x] Crear `app/backend/routers/recipes.py`
- [x] `GET /recipes` con filtros opcionales: `?category_id=`, `?subcategory_id=`, `?search=`
- [x] `GET /recipes/{id}` con ingredientes incluidos
- [x] `POST /recipes` — flujo completo:
  1. Recibir `RecipeCreate` con lista de ingredientes
  2. Para cada ingrediente: traducir nombre a inglés (GPT-4o mini) → consultar USDA → guardar macros en `RecipeIngredient`
  3. Calcular macros totales de la receta → guardar en `Recipe`
  4. Devolver `RecipeRead`
- [x] `PUT /recipes/{id}` — recalcular macros si cambian ingredientes
- [x] `DELETE /recipes/{id}` — eliminar en cascada (ingredientes)
- [x] `POST /recipes/suggest` — recibir lista de ingredientes, llamar a OpenAI, devolver borrador
- [x] `GET /recipes/images?query=` — buscar en Unsplash, devolver lista de URLs
- [x] Registrar router en `app/backend/main.py`
- [x] Testar todos los endpoints en Swagger UI

### Router de categorías
- [x] Crear `app/backend/routers/categories.py`
- [x] `GET /categories` — árbol completo (categorías con sus subcategorías)
- [x] `POST /categories`, `PUT /categories/{id}`, `DELETE /categories/{id}`
- [x] `POST /categories/{id}/subcategories`, `PUT /subcategories/{id}`, `DELETE /subcategories/{id}`
- [x] Registrar router en `app/backend/main.py`

---

## FASE 3 — Backend: Menú Semanal

> **Objetivo:** El menú semanal se puede crear, consultar, modificar y autorellenar.  
> **Dependencias:** FASE 2 completa  
> **Duración estimada:** 1-2 sesiones

### Lógica core
- [x] Crear `app/core/menu_generator.py`
  - [x] Función `get_slot_macro_budget(day_macros: MacroTotals, slot_type: SlotType, target: MacroTotals) -> MacroTotals`
  - [x] Función `filter_compatible_recipes(recipes: list[Recipe], slot_type: SlotType, budget: MacroTotals) -> list[Recipe]`
  - [x] Función `autofill_week(week: MenuWeek, recipes: list[Recipe], target: MacroTotals) -> list[SlotUpdate]`
  - [x] Tests básicos de la lógica en `app/core/tests/test_menu_generator.py`

### Router de menú
- [x] Crear `app/backend/routers/menu.py`
- [x] `GET /menu/weeks` — listar semanas con resumen (fecha, % completitud)
- [x] `GET /menu/week/{week_start}` — semana completa con:
  - Slots con recetas y sus macros
  - Extras del día con sus macros
  - Macros totales por día (`DayMacrosSummary`)
- [x] `POST /menu/week` — crear semana nueva (genera los 5 días con 5 slots vacíos cada uno)
- [x] `PUT /menu/slot/{slot_id}` — asignar `recipe_id` (o `null` para vaciar)
- [x] `DELETE /menu/slot/{slot_id}` — alias de PUT con recipe_id=null
- [x] `POST /menu/week/{week_start}/autofill` — rellenar solo los slots vacíos
- [x] Registrar router en `app/backend/main.py`

### Router de extras
- [x] Crear `app/backend/routers/extras.py`
- [x] `GET /extras` — listar todos los extras predefinidos
- [x] `POST /extras`, `PUT /extras/{id}`, `DELETE /extras/{id}`
- [x] `POST /menu/day/{day_id}/extras` — añadir extra al día con `quantity`
- [x] `DELETE /menu/day-extra/{id}` — quitar extra del día
- [x] Registrar router en `app/backend/main.py`

---

## FASE 4 — Backend: Perfil y TDEE

> **Objetivo:** El perfil calcula TDEE/BMR automáticamente y define los targets de macros.  
> **Dependencias:** FASE 1 completa  
> **Duración estimada:** 0.5 sesiones (módulo pequeño)

- [x] Crear `app/core/tdee.py`
  - [x] Función `calculate_bmr(weight_kg, height_cm, age, gender) -> float` — fórmula Mifflin-St Jeor
  - [x] Función `calculate_tdee(bmr, activity_level: ActivityLevel) -> float` — multiplicadores
  - [x] Función `apply_goal(tdee, goal: Goal) -> float` — déficit/mantenimiento/superávit
  - [x] Tests en `app/core/tests/test_tdee.py`
- [x] Crear `app/core/macro_targets.py`
  - [x] Función `calculate_macro_grams(kcal_target, prot_pct, hc_pct, fat_pct) -> MacroGrams`
  - [x] Fórmula: prot_g = (kcal_target * prot_pct/100) / 4 ; hc_g / 4 ; fat_g / 9
- [x] Crear `app/backend/routers/profile.py`
  - [x] `GET /profile` — devolver perfil actual con todos los targets calculados
  - [x] `PUT /profile` — actualizar, recalcular TDEE y macro_g_targets, guardar en BD
  - [x] `POST /profile/calculate-tdee` — preview sin guardar (útil para la UI en tiempo real)
- [x] Registrar router en `app/backend/main.py`
- [x] Testar en Swagger: modificar perfil y verificar que kcal_target se recalcula

---

## FASE 5 — Frontend: Estructura Base

> **Objetivo:** App Flet navega entre 3 pantallas. Cliente HTTP conecta con el backend.  
> **Dependencias:** FASE 0 + FASE 1 (necesita la BD con seed)  
> **Duración estimada:** 1 sesión

- [ ] Actualizar `app/frontend/api_client.py`
  - [ ] Métodos async: `get()`, `post()`, `put()`, `delete()`
  - [ ] Manejo de errores HTTP con excepciones tipadas
  - [ ] Base URL configurable desde `.env` (en la raíz del proyecto)
- [ ] Definir tema Material Design 3 en `app/frontend/main.py`
  - [ ] Color primario (verde o naranja — sugerencia: `#4CAF50` o `#FF7043`)
  - [ ] Fuente: Roboto (default de Flet)
  - [ ] Modo claro/oscuro (opcional MVP: solo modo claro)
- [ ] Crear layout principal con `ft.NavigationBar` (3 tabs: Recetas / Menú / Ajustes)
- [ ] Implementar routing básico entre vistas (cambiar `page.views` al cambiar tab)
- [ ] Crear vistas placeholder para las 3 pantallas con título y mensaje "En construcción"
- [ ] Implementar `ft.ResponsiveRow` como contenedor base (adaptable a ancho de ventana)
- [ ] Verificar que la navegación entre tabs funciona sin errores

---

## FASE 6 — Frontend: Pantalla A (Gestión de Recetas)

> **Objetivo:** El usuario puede ver, crear, editar y eliminar recetas con imagen y macros.  
> **Dependencias:** FASE 2 + FASE 5  
> **Duración estimada:** 2-3 sesiones

### Componentes reutilizables
- [ ] Crear `app/frontend/components/recipe_card.py`
  - [ ] Imagen (con fallback si no hay URL)
  - [ ] Nombre y subcategoría
  - [ ] Macros resumen (kcal, prot, hc, fat) en chips pequeños
  - [ ] Botones editar/eliminar en hover
- [ ] Crear `app/frontend/components/image_carousel.py`
  - [ ] Mostrar 3-5 imágenes en fila horizontal scrollable
  - [ ] Estado "seleccionada" (borde/overlay al hacer click)
  - [ ] Loading state mientras carga Unsplash
- [ ] Crear `app/frontend/components/macro_progress_bar.py`
  - [ ] 4 barras: kcal, prot, hc, fat
  - [ ] Colores distintos por macro
  - [ ] Mostrar valor actual / objetivo y porcentaje

### Vista principal de recetas
- [ ] Crear `app/frontend/views/recipes_view.py`
  - [ ] Grid responsivo de `RecipeCard` (2 cols en móvil, 3-4 en escritorio)
  - [ ] Chips de filtro horizontal (categorías) — scroll horizontal si hay muchas
  - [ ] Sub-chips de subcategoría (aparecen al seleccionar categoría)
  - [ ] Campo de búsqueda por nombre
  - [ ] FAB (+) en esquina inferior derecha
  - [ ] Empty state con mensaje si no hay recetas
  - [ ] Loading state al cargar

### Formulario de receta
- [ ] Crear `app/frontend/views/recipe_form.py`
  - [ ] Campos: nombre, categoría (dropdown), subcategoría (dropdown), raciones
  - [ ] Campo de instrucciones (textarea multilínea)
  - [ ] Sección ingredientes dinámica:
    - [ ] Botón "Añadir ingrediente" → fila con (nombre, cantidad en gramos)
    - [ ] Botón eliminar por fila
    - [ ] Mínimo 1 ingrediente para poder guardar
  - [ ] Sección imagen:
    - [ ] Botón "Buscar imágenes" → llama a `/recipes/images` → muestra `ImageCarousel`
    - [ ] Campo URL manual como alternativa
  - [ ] Botón "Guardar" → llama a POST/PUT → muestra macros calculados en un snackbar
  - [ ] Modo edición (pre-rellena campos con datos existentes)

### Despensa Virtual
- [ ] Añadir botón "Sugerir receta" en la vista de recetas (junto al FAB o en el FAB expandido)
- [ ] Modal/bottom sheet: input de ingredientes disponibles (chips añadibles)
- [ ] Botón "Sugerir" → llama a `/recipes/suggest` → loading state
- [ ] Resultado: abre el formulario de receta pre-rellenado con la sugerencia de GPT
- [ ] Usuario revisa y puede editar antes de guardar

---

## FASE 7 — Frontend: Pantalla B (Menú Semanal)

> **Objetivo:** El usuario puede gestionar el menú semanal y ver macros por día.  
> **Dependencias:** FASE 3 + FASE 5  
> **Duración estimada:** 2-3 sesiones

### Vista principal del menú
- [ ] Crear `app/frontend/views/menu_view.py`
  - [ ] Cabecera con: semana actual (ej: "3-7 Jun 2025"), flechas ← →
  - [ ] Grid 5 columnas (L-V) × 5 filas (slots) — o vista apilada en móvil
  - [ ] Cada celda muestra: nombre receta (truncado) + kcal, o "+" si vacía
  - [ ] Tap en celda vacía → bottom sheet selector de receta
  - [ ] Tap en celda con receta → opciones: cambiar / quitar
  - [ ] Botón "Rellenar huecos" (llamar a autofill) con loading state
  - [ ] Tap en cabecera de día (Lunes, Martes...) → `DayDetailView`
  - [ ] Indicador de % de kcal diarias completadas bajo cada columna de día

### Selector de receta
- [ ] Bottom sheet con búsqueda de recetas por nombre
- [ ] Filtro por categoría compatible con el slot seleccionado
- [ ] Cada resultado muestra nombre + kcal + macros para decidir rápido

### Detalle de día
- [ ] Crear `app/frontend/views/day_detail_view.py`
  - [ ] Título con fecha del día
  - [ ] Lista de slots con: nombre slot, nombre receta, macros de esa receta
  - [ ] `MacroProgressBar` con totales del día vs objetivo del perfil
  - [ ] Sección "Extras del día":
    - [ ] Lista de extras ya añadidos con cantidad y sus macros
    - [ ] Botón "+" → lista de extras predefinidos (del GET /extras)
    - [ ] Cada extra tiene stepper de cantidad (×1, ×2, etc.)
    - [ ] Macros del `MacroProgressBar` se actualizan en tiempo real

---

## FASE 8 — Frontend: Pantalla C (Ajustes)

> **Objetivo:** El usuario configura su perfil, objetivos y gestiona categorías/extras.  
> **Dependencias:** FASE 4 + FASE 5  
> **Duración estimada:** 1-2 sesiones

- [ ] Crear `app/frontend/views/settings_view.py` (abierta como modal o drawer)
- [ ] **Sección Perfil y Objetivos**
  - [ ] Campos: peso, altura, edad
  - [ ] Selector género (Radio buttons: Hombre / Mujer)
  - [ ] Selector nivel de actividad (Dropdown con 5 opciones)
  - [ ] Selector objetivo (Déficit / Mantenimiento / Superávit)
  - [ ] Preview TDEE en tiempo real (llamar a `POST /profile/calculate-tdee`)
  - [ ] Sliders para ratio de macros (prot% / hc% / fat%) con suma visible
  - [ ] Validación: los 3 porcentajes deben sumar exactamente 100%
  - [ ] Botón "Guardar perfil"
- [ ] **Sección Categorías**
  - [ ] Lista de categorías con botón editar/eliminar
  - [ ] Expandir categoría → lista de subcategorías editables
  - [ ] Botón "Nueva categoría" → formulario inline
  - [ ] Botón "Nueva subcategoría" por categoría
- [ ] **Sección Extras Rápidos**
  - [ ] Lista de extras predefinidos con sus macros
  - [ ] Botón editar/eliminar por extra
  - [ ] Formulario "Nuevo extra": nombre, kcal, prot, hc, fat

---

## FASE 9 — Polish y Testing

> **Objetivo:** La app es robusta, manejable y agradable de usar.  
> **Dependencias:** TODAS las fases anteriores  
> **Duración estimada:** 1-2 sesiones

### Robustez
- [ ] Manejo global de errores HTTP en `api_client.py` → mostrar snackbar de error
- [ ] Loading states en TODAS las llamadas async (ninguna debería bloquearse silenciosamente)
- [ ] Empty states con mensajes útiles en: listado de recetas, días del menú vacíos
- [ ] Validaciones completas en todos los formularios:
  - [ ] Receta: nombre obligatorio, mínimo 1 ingrediente, cantidades > 0
  - [ ] Perfil: peso/altura/edad en rangos razonables, porcentajes suman 100%
  - [ ] Extras: nombre obligatorio, kcal > 0

### Caché de ingredientes (mejora USDA + traducción)
- [ ] Añadir tabla `IngredientCache` en BD: `(name_normalized, name_en, kcal_100g, prot_100g, hc_100g, fat_100g)`
- [ ] En `app/backend/services/usda.py`: antes de traducir y llamar a USDA, buscar en BD → si existe, devolver sin llamadas externas
- [ ] Normalizar nombre: minúsculas + strip → evitar duplicados por capitalización
- [ ] La caché en BD persiste entre reinicios del servidor (distinta de la `_translation_cache` en memoria)

### Testing end-to-end
- [ ] Flujo 1: Crear receta manualmente → verificar macros calculados → asignar a menú
- [ ] Flujo 2: Despensa Virtual → sugerir receta → revisar → guardar → asignar a menú
- [ ] Flujo 3: Autofill semana vacía → verificar que no excede macros diarios
- [ ] Flujo 4: Añadir extras a un día → verificar que el `MacroProgressBar` se actualiza
- [ ] Flujo 5: Cambiar perfil (más calorías) → verificar que las barras de macros reflejan el cambio

### Documentación
- [ ] Actualizar `README.md` con:
  - [ ] Instrucciones de instalación y setup
  - [ ] Cómo configurar las APIs (link a `03_APIS_EXTERNAS.md`)
  - [ ] Cómo arrancar backend y frontend
  - [ ] Capturas de pantalla (opcional)
