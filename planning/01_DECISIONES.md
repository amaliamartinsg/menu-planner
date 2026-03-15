# 📋 01 — Decisiones Técnicas y de Diseño

> Registro de todas las decisiones tomadas durante la fase de planificación.
> Consultar antes de implementar cualquier módulo.

---

## Stack Tecnológico

| Capa | Tecnología | Justificación |
|---|---|---|
| Backend | **FastAPI** | Async nativo, validación Pydantic integrada, Swagger automático |
| Base de datos | **SQLite + SQLModel** | Sin servidor, perfecto para uso local; SQLModel unifica modelos BD + Pydantic |
| Frontend | **React 18 + TypeScript + Vite** | Ecosistema maduro, tipado end-to-end con los schemas Pydantic, HMR ultrarrápido |
| UI Components | **Material UI (MUI) v5** | Implementación fiel de Material Design 3, ampliamente documentada |
| Routing | **React Router v6** | Estándar de facto para SPAs React |
| Estado servidor | **TanStack Query v5** | Cache + loading/error states automáticos para todas las llamadas API |
| HTTP client | **Axios** | Interceptores globales de error, tipado sencillo |
| Comunicación | **HTTP REST** | FastAPI en `localhost:8000` + React dev server en `localhost:5173` |
| Macros ingredientes | **USDA FoodData Central** | Completamente gratuita y sin límite diario práctico |
| Imágenes | **Unsplash API** | Gratuita (50 req/hora), alta calidad |
| IA Despensa Virtual | **OpenAI GPT-4o mini** | Muy barato (~0.15$/1M tokens), buena calidad para recetas |

---

## Decisiones de Arquitectura

### ¿Por qué FastAPI separado + React como cliente?
- Permite testear la API con Swagger UI (`/docs`) de forma independiente
- Separación clara de responsabilidades (backend vs frontend)
- React corre en el navegador — funciona como SPA real sin runtime de escritorio
- El coste en complejidad para uso local es mínimo (dos terminales: uvicorn + vite dev)
- CORS configurado en FastAPI para `http://localhost:5173` (Vite dev server)

### ¿Por qué SQLModel sobre SQLAlchemy puro?
- Unifica modelos de BD y schemas Pydantic en una sola clase
- Elimina duplicación de código (no hay que mantener dos definiciones del mismo modelo)
- Mismo autor que FastAPI (Tiangolo) → integración perfecta
- Migraciones simples con `create_all()` para el MVP

### ¿Por qué `app/core/` separado del `app/backend/`?
- `app/core/` contiene lógica pura de dominio sin imports de FastAPI ni SQLModel
- Testeable de forma aislada con pytest simple
- Reutilizable si se cambia el framework en el futuro
- Módulos en `app/core/`: cálculos TDEE, conversión macros, algoritmo generador de menú

### ¿Por qué USDA FoodData Central para macros?
- Completamente gratuita, sin límite diario práctico ni tarjeta requerida
- Base de datos oficial del gobierno de EE.UU. — alta fiabilidad para ingredientes crudos
- Los nombres en español se traducen automáticamente a inglés con GPT-4o mini antes de consultar
- **Mejora planificada en Fase 9**: añadir caché en SQLite — si el mismo ingrediente ya fue consultado, reutilizar resultado sin llamadas externas

---

## Decisiones de Producto

### Autenticación
- **Sin auth** — perfil único local
- Una sola fila en tabla `Profile` (id=1)
- Si en el futuro se necesita multi-usuario, se añade columna `user_id` a todas las tablas

### Slots del menú diario
Los 5 slots son **fijos** (no configurables en el MVP):
1. Desayuno
2. Media mañana
3. Comida
4. Merienda
5. Cena

### Semanas del menú
- Se guarda **histórico completo** de semanas anteriores
- Identificadas por `week_start_date` (siempre un lunes)
- Navegación entre semanas en la UI (flechas anterior/siguiente)

### Categorías de recetas
- **Completamente personalizables** desde la app
- Estructura: `Categoría → Subcategoría → Receta`
- Categorías por defecto precargadas en el seed (editables):
  - Desayuno (Dulce, Salado)
  - Comida (Pasta, Arroz, Carne, Pescado, Legumbres, Ensalada)
  - Cena (Ligera, Completa)
  - Snack (Dulce, Salado)

### Instrucciones de receta
- **Texto libre** dentro de la app (campo `instructions_text`)
- Sin links externos en el MVP

### Extras Rápidos
- **Lista de items predefinidos reutilizables** (tabla `Extra` en BD)
- El usuario crea sus extras una vez (ej: "Café con leche = 80kcal / 3g prot / 8g hc / 3g fat")
- En el menú diario, marca qué extras consume ese día (con cantidad/multiplicador)

### Objetivo calórico
- Calculador **TDEE/BMR integrado** con fórmula Mifflin-St Jeor
- Campos del perfil: peso (kg), altura (cm), edad, género, nivel de actividad
- 5 niveles de actividad: Sedentario, Ligero, Moderado, Activo, Muy activo
- Objetivo: Déficit (-500 kcal) / Mantenimiento / Superávit (+300 kcal)
- Ratios de macros configurables en porcentajes (deben sumar 100%)

---

## Decisiones de UX/UI

- **Material Design 3** mediante Material UI (MUI) v5
- Navegación principal: `<BottomNavigation>` de MUI con 3 tabs
  - 🍽️ Recetas
  - 📅 Menú
  - ⚙️ Ajustes
- Diseño **responsivo** con el sistema Grid de MUI (`xs/sm/md` breakpoints)
- Ajustes accesibles via `<Dialog>` modal (no ruta nueva) desde el icono de engranaje
- Loading states con `CircularProgress` y skeleton en todas las llamadas al backend
- TanStack Query gestiona cache, revalidación y estados loading/error automáticamente

---

## Limitaciones Conocidas del MVP

| Limitación | Solución futura |
|---|---|
| USDA: base de datos en inglés | Traducción automática con GPT-4o mini (ya implementado) |
| Sin búsqueda de recetas por texto libre | Añadir full-text search con SQLite FTS5 |
| OpenAI requiere saldo | Migrar a Ollama local si el coste molesta |
| Sin sincronización cloud | Exportar/importar DB como backup |
| Solo L-V en el menú | Ampliar a L-D si se necesita |
