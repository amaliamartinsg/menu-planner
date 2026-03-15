# 📋 01 — Decisiones Técnicas y de Diseño

> Registro de todas las decisiones tomadas durante la fase de planificación.
> Consultar antes de implementar cualquier módulo.

---

## Stack Tecnológico

| Capa | Tecnología | Justificación |
|---|---|---|
| Backend | **FastAPI** | Async nativo, validación Pydantic integrada, Swagger automático |
| Base de datos | **SQLite + SQLModel** | Sin servidor, perfecto para uso local; SQLModel unifica modelos BD + Pydantic |
| Frontend | **Flet** | Python puro, Material Design 3, multiplataforma |
| Comunicación | **HTTP (httpx)** | FastAPI server en `localhost:8000` + Flet como cliente HTTP |
| Macros ingredientes | **USDA FoodData Central** | Completamente gratuita y sin límite diario práctico |
| Imágenes | **Unsplash API** | Gratuita (50 req/hora), alta calidad |
| IA Despensa Virtual | **OpenAI GPT-4o mini** | Muy barato (~0.15$/1M tokens), buena calidad para recetas |

---

## Decisiones de Arquitectura

### ¿Por qué FastAPI separado + Flet como cliente?
- Permite testear la API con Swagger UI (`/docs`) de forma independiente
- Separación clara de responsabilidades (backend vs frontend)
- Reutilizable si en el futuro se hace versión web o móvil real
- El coste en complejidad para uso local es mínimo (dos terminales)

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

- **Material Design 3** mediante Flet
- Navegación principal: Bottom Navigation Bar con 3 tabs
  - 🍽️ Recetas
  - 📅 Menú
  - ⚙️ Ajustes
- Diseño **responsivo** con `ft.ResponsiveRow` (adaptable a ventana pequeña tipo móvil)
- Ajustes accesibles via **Modal** (no pantalla nueva) desde el icono de engranaje
- Loading states en todas las llamadas async al backend

---

## Limitaciones Conocidas del MVP

| Limitación | Solución futura |
|---|---|
| USDA: base de datos en inglés | Traducción automática con GPT-4o mini (ya implementado) |
| Sin búsqueda de recetas por texto libre | Añadir full-text search con SQLite FTS5 |
| OpenAI requiere saldo | Migrar a Ollama local si el coste molesta |
| Sin sincronización cloud | Exportar/importar DB como backup |
| Solo L-V en el menú | Ampliar a L-D si se necesita |
