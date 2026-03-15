# 🏗️ 02 — Arquitectura y Modelos de Datos

---

## Estructura de Directorios

```
pyplanner/                             # Raíz del proyecto
│
├── planning/                          # ← Esta carpeta (documentación)
├── .env                               # API keys — NUNCA subir a git
├── .env.example                       # Plantilla de variables de entorno
├── .gitignore
├── requirements.txt
└── README.md
│
└── app/                               # Toda la aplicación vive aquí
    │
    ├── backend/                       # FastAPI server (puerto 8000)
    │   ├── main.py                    # Entry point, CORS, registro de routers
    │   ├── database.py                # SQLite engine + get_session()
    │   ├── models/                    # SQLModel — definición de tablas
    │   │   ├── __init__.py
    │   │   ├── category.py            # Category, SubCategory
    │   │   ├── recipe.py              # Recipe, RecipeIngredient
    │   │   ├── menu.py                # MenuWeek, MenuDay, MenuSlot
    │   │   ├── extra.py               # Extra, MenuDayExtra
    │   │   └── profile.py             # Profile (tabla de 1 fila)
    │   ├── schemas/                   # Pydantic — request/response DTOs
    │   │   ├── __init__.py
    │   │   ├── recipe.py              # RecipeCreate, RecipeRead, RecipeUpdate
    │   │   ├── menu.py                # MenuWeekRead, SlotUpdate, DayMacros
    │   │   ├── category.py            # CategoryCreate, CategoryRead
    │   │   ├── extra.py               # ExtraCreate, ExtraRead
    │   │   └── profile.py             # ProfileUpdate, ProfileRead
    │   ├── routers/                   # Endpoints agrupados por dominio
    │   │   ├── __init__.py
    │   │   ├── recipes.py             # /recipes/*
    │   │   ├── menu.py                # /menu/*
    │   │   ├── categories.py          # /categories/*
    │   │   ├── extras.py              # /extras/*
    │   │   └── profile.py             # /profile
    │   └── services/                  # Lógica de negocio + integraciones externas
    │       ├── __init__.py
    │       ├── usda.py                # USDA FoodData Central — macros por ingrediente
    │       ├── unsplash.py            # Image Search API
    │       ├── openai_service.py      # GPT-4o mini — Despensa Virtual
    │       └── macro_calculator.py    # Suma macros de ingredientes → receta
    │
    ├── core/                          # Lógica pura (sin deps de FastAPI/SQLModel)
    │   ├── __init__.py
    │   ├── tdee.py                    # Fórmula Mifflin-St Jeor + multiplicadores
    │   ├── macro_targets.py           # kcal_target + porcentajes → gramos
    │   ├── menu_generator.py          # Algoritmo relleno inteligente de huecos
    │   └── tests/
    │       ├── __init__.py
    │       ├── test_tdee.py
    │       └── test_menu_generator.py
    │
    ├── frontend/                      # Flet app (se ejecuta por separado)
    │   ├── main.py                    # Entry point Flet + routing
    │   ├── api_client.py              # Cliente HTTP (httpx) → localhost:8000
    │   ├── views/
    │   │   ├── __init__.py
    │   │   ├── recipes_view.py        # Pantalla A: grid + filtros de categoría
    │   │   ├── recipe_form.py         # Formulario crear/editar receta
    │   │   ├── menu_view.py           # Pantalla B: grid L-V × 5 slots
    │   │   ├── day_detail_view.py     # Detalle día: macros + extras
    │   │   └── settings_view.py       # Pantalla C: perfil + categorías + extras
    │   └── components/                # Widgets Flet reutilizables
    │       ├── __init__.py
    │       ├── recipe_card.py         # Tarjeta receta (imagen, nombre, macros)
    │       ├── macro_progress_bar.py  # Barra progreso prot/hc/fat/kcal vs objetivo
    │       ├── image_carousel.py      # Carrusel selección imagen (3-5 fotos)
    │       └── extra_quick_panel.py   # Panel lateral extras rápidos
    │
    └── data/
        └── seed.py                    # Script de datos iniciales (categorías, perfil)
```

---

## Modelos de Datos (SQLModel)

### Relaciones

```
Profile          (tabla única, id=1)
    └── define kcal_target, macro ratios

Category (1) ──→ (N) SubCategory
SubCategory (1) ──→ (N) Recipe
Recipe (1) ──→ (N) RecipeIngredient
    └── macros calculados por USDA al guardar

MenuWeek (1) ──→ (5) MenuDay  [Lun-Vie]
MenuDay  (1) ──→ (5) MenuSlot [Desayuno, MediaMañana, Comida, Merienda, Cena]
MenuSlot (N) ──→ (1) Recipe   [nullable — slot vacío]

Extra           (tabla de items reutilizables)
MenuDay (1) ──→ (N) MenuDayExtra ──→ (1) Extra
    └── con campo `quantity` (multiplicador)
```

### Definición de Modelos

#### `Category` y `SubCategory`
```python
class Category(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    color: str | None = None          # Hex color para UI (#FF5733)
    subcategories: list["SubCategory"] = Relationship(back_populates="category")

class SubCategory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    category_id: int = Field(foreign_key="category.id")
    category: Category = Relationship(back_populates="subcategories")
```

#### `Recipe` y `RecipeIngredient`
```python
class Recipe(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    subcategory_id: int | None = Field(default=None, foreign_key="subcategory.id")
    instructions_text: str | None = None
    image_url: str | None = None
    servings: int = Field(default=1)
    # Macros TOTALES de la receta (suma de ingredientes)
    kcal: float = Field(default=0)
    prot_g: float = Field(default=0)
    hc_g: float = Field(default=0)
    fat_g: float = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ingredients: list["RecipeIngredient"] = Relationship(back_populates="recipe")

class RecipeIngredient(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    recipe_id: int = Field(foreign_key="recipe.id")
    name: str                         # "Pechuga de pollo"
    quantity_g: float                 # 150.0 (gramos)
    # Macros por 100g (devueltos por USDA, guardados para recálculo)
    kcal_100g: float = Field(default=0)
    prot_100g: float = Field(default=0)
    hc_100g: float = Field(default=0)
    fat_100g: float = Field(default=0)
    recipe: Recipe = Relationship(back_populates="ingredients")
```

#### `MenuWeek`, `MenuDay`, `MenuSlot`
```python
class SlotType(str, Enum):
    DESAYUNO = "desayuno"
    MEDIA_MANANA = "media_manana"
    COMIDA = "comida"
    MERIENDA = "merienda"
    CENA = "cena"

class MenuWeek(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    week_start: date                  # Siempre lunes
    label: str | None = None          # Etiqueta opcional ("Semana cutting")
    days: list["MenuDay"] = Relationship(back_populates="week")

class MenuDay(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    week_id: int = Field(foreign_key="menuweek.id")
    day_date: date
    week: MenuWeek = Relationship(back_populates="days")
    slots: list["MenuSlot"] = Relationship(back_populates="day")
    day_extras: list["MenuDayExtra"] = Relationship(back_populates="day")

class MenuSlot(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    day_id: int = Field(foreign_key="menuday.id")
    slot_type: SlotType
    recipe_id: int | None = Field(default=None, foreign_key="recipe.id")
    day: MenuDay = Relationship(back_populates="slots")
    recipe: Recipe | None = Relationship()
```

#### `Extra` y `MenuDayExtra`
```python
class Extra(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str                         # "Café con leche", "Manzana", "Whey"
    kcal: float
    prot_g: float = Field(default=0)
    hc_g: float = Field(default=0)
    fat_g: float = Field(default=0)

class MenuDayExtra(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    day_id: int = Field(foreign_key="menuday.id")
    extra_id: int = Field(foreign_key="extra.id")
    quantity: float = Field(default=1.0)   # Multiplicador (2 = doble porción)
    day: MenuDay = Relationship(back_populates="day_extras")
    extra: Extra = Relationship()
```

#### `Profile`
```python
class ActivityLevel(str, Enum):
    SEDENTARY = "sedentary"            # x1.2
    LIGHT = "light"                    # x1.375
    MODERATE = "moderate"              # x1.55
    ACTIVE = "active"                  # x1.725
    VERY_ACTIVE = "very_active"        # x1.9

class Goal(str, Enum):
    DEFICIT = "deficit"                # TDEE - 500 kcal
    MAINTAIN = "maintain"              # TDEE
    SURPLUS = "surplus"                # TDEE + 300 kcal

class Profile(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)   # Siempre id=1
    weight_kg: float = Field(default=75)
    height_cm: float = Field(default=175)
    age: int = Field(default=30)
    gender: str = Field(default="male")            # "male" | "female"
    activity_level: ActivityLevel = Field(default=ActivityLevel.MODERATE)
    goal: Goal = Field(default=Goal.MAINTAIN)
    # Calculados y guardados al actualizar perfil
    kcal_target: float = Field(default=2000)
    prot_pct: float = Field(default=30)            # % proteína
    hc_pct: float = Field(default=45)             # % hidratos
    fat_pct: float = Field(default=25)             # % grasas
    # En gramos (calculados de kcal_target + porcentajes)
    prot_g_target: float = Field(default=150)
    hc_g_target: float = Field(default=225)
    fat_g_target: float = Field(default=56)
```

---

## Endpoints de la API (resumen)

### Recetas
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/recipes` | Listado con filtros `?category_id=&subcategory_id=&search=` |
| GET | `/recipes/{id}` | Detalle de una receta |
| POST | `/recipes` | Crear receta (triggerea cálculo macros vía USDA) |
| PUT | `/recipes/{id}` | Editar receta |
| DELETE | `/recipes/{id}` | Eliminar receta |
| POST | `/recipes/suggest` | Despensa Virtual — GPT-4o mini |
| GET | `/recipes/images` | Búsqueda imágenes `?query=` (Unsplash) |

### Categorías
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/categories` | Listado con subcategorías anidadas |
| POST | `/categories` | Crear categoría |
| PUT | `/categories/{id}` | Editar categoría |
| DELETE | `/categories/{id}` | Eliminar categoría |
| POST | `/categories/{id}/subcategories` | Crear subcategoría |
| PUT | `/subcategories/{id}` | Editar subcategoría |
| DELETE | `/subcategories/{id}` | Eliminar subcategoría |

### Menú
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/menu/weeks` | Listar semanas guardadas |
| GET | `/menu/week/{week_start}` | Semana completa con macros calculados |
| POST | `/menu/week` | Crear nueva semana |
| PUT | `/menu/slot/{slot_id}` | Asignar/cambiar receta a un slot |
| DELETE | `/menu/slot/{slot_id}` | Vaciar slot |
| POST | `/menu/week/{week_start}/autofill` | Generador inteligente de huecos |
| POST | `/menu/day/{day_id}/extras` | Añadir extra a un día |
| DELETE | `/menu/day-extra/{id}` | Quitar extra de un día |

### Extras
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/extras` | Listar extras predefinidos |
| POST | `/extras` | Crear extra |
| PUT | `/extras/{id}` | Editar extra |
| DELETE | `/extras/{id}` | Eliminar extra |

### Perfil
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/profile` | Obtener perfil actual |
| PUT | `/profile` | Actualizar perfil (recalcula TDEE y targets) |
| POST | `/profile/calculate-tdee` | Preview TDEE sin guardar |

---

## Lógica del Generador de Menú Inteligente

```
POST /menu/week/{week_start}/autofill

Para cada día (L-V):
  Para cada slot vacío del día:
    1. Calcular macros ya consumidos (slots ocupados + extras del día)
    2. Calcular "presupuesto restante" = target_diario - consumido
        └── El target por slot = target_diario / 5 (simplificación MVP)
    3. Filtrar recetas por categoría compatible con el slot_type
        └── Desayuno → cat "Desayuno", Comida → cat "Comida", etc.
    4. De las recetas que caben en el presupuesto restante, elegir aleatoriamente
    5. Si no hay ninguna que quepa, elegir la de menor kcal disponible
    6. Asignar recipe_id al slot
```
