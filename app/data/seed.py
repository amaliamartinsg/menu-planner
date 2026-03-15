"""Initial data seed for PyPlanner.

Run once to populate the database with default categories, profile,
sample extras and sample recipes.

Usage:
    python app/data/seed.py
"""

import sys
from pathlib import Path

# Allow running as a script from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.backend.database import create_db_and_tables, get_session
from app.backend.models.category import Category, SubCategory
from app.backend.models.extra import Extra
from app.backend.models.profile import ActivityLevel, Goal, Profile
from app.backend.models.recipe import Recipe, RecipeIngredient


# ---------------------------------------------------------------------------
# Default categories and subcategories
# ---------------------------------------------------------------------------

CATEGORIES: list[dict] = [
    {
        "name": "Desayuno",
        "color": "#FF8C00",
        "subcategories": ["Dulce", "Salado"],
    },
    {
        "name": "Comida",
        "color": "#4CAF50",
        "subcategories": ["Pasta", "Arroz", "Carne", "Pescado", "Legumbres", "Ensalada"],
    },
    {
        "name": "Cena",
        "color": "#5C6BC0",
        "subcategories": ["Ligera", "Completa"],
    },
    {
        "name": "Snack",
        "color": "#F06292",
        "subcategories": ["Dulce", "Salado"],
    },
]

# ---------------------------------------------------------------------------
# Default extras
# ---------------------------------------------------------------------------

EXTRAS: list[dict] = [
    {"name": "Café con leche", "kcal": 80, "prot_g": 3.0, "hc_g": 8.0, "fat_g": 3.0},
    {"name": "Fruta (pieza mediana)", "kcal": 60, "prot_g": 0.5, "hc_g": 14.0, "fat_g": 0.2},
    {"name": "Whey protein (1 scoop)", "kcal": 120, "prot_g": 24.0, "hc_g": 3.0, "fat_g": 1.5},
    {"name": "Almendras (20g)", "kcal": 116, "prot_g": 4.0, "hc_g": 2.0, "fat_g": 10.0},
    {"name": "Yogur natural", "kcal": 70, "prot_g": 5.0, "hc_g": 6.0, "fat_g": 2.0},
]

# ---------------------------------------------------------------------------
# Sample recipes (macros are pre-filled; in production USDA computes them)
# ---------------------------------------------------------------------------

RECIPES: list[dict] = [
    {
        "name": "Tortilla de avena con plátano",
        "kcal": 380,
        "prot_g": 22.0,
        "hc_g": 48.0,
        "fat_g": 9.0,
        "servings": 1,
        "instructions_text": (
            "1. Mezcla 60g de copos de avena con 2 huevos y medio plátano triturado.\n"
            "2. Cocina en sartén antiadherente a fuego medio 3 min por lado.\n"
            "3. Sirve con un chorrito de miel opcional."
        ),
        "subcategory_name": "Dulce",
        "category_name": "Desayuno",
        "ingredients": [
            {"name": "Copos de avena", "quantity_g": 60, "kcal_100g": 368, "prot_100g": 13.0, "hc_100g": 58.0, "fat_100g": 7.0},
            {"name": "Huevo", "quantity_g": 100, "kcal_100g": 155, "prot_100g": 13.0, "hc_100g": 1.1, "fat_100g": 11.0},
            {"name": "Plátano", "quantity_g": 60, "kcal_100g": 89, "prot_100g": 1.1, "hc_100g": 23.0, "fat_100g": 0.3},
        ],
    },
    {
        "name": "Pollo al horno con verduras",
        "kcal": 420,
        "prot_g": 45.0,
        "hc_g": 18.0,
        "fat_g": 16.0,
        "servings": 1,
        "instructions_text": (
            "1. Precalienta el horno a 200°C.\n"
            "2. Adereza la pechuga con aceite, ajo, sal y romero.\n"
            "3. Hornea junto a las verduras troceadas durante 30-35 min."
        ),
        "subcategory_name": "Carne",
        "category_name": "Comida",
        "ingredients": [
            {"name": "Pechuga de pollo", "quantity_g": 200, "kcal_100g": 165, "prot_100g": 31.0, "hc_100g": 0.0, "fat_100g": 3.6},
            {"name": "Pimiento rojo", "quantity_g": 100, "kcal_100g": 31, "prot_100g": 1.0, "hc_100g": 6.0, "fat_100g": 0.3},
            {"name": "Calabacín", "quantity_g": 120, "kcal_100g": 17, "prot_100g": 1.2, "hc_100g": 3.1, "fat_100g": 0.3},
            {"name": "Aceite de oliva", "quantity_g": 10, "kcal_100g": 884, "prot_100g": 0.0, "hc_100g": 0.0, "fat_100g": 100.0},
        ],
    },
    {
        "name": "Ensalada de atún con garbanzos",
        "kcal": 350,
        "prot_g": 30.0,
        "hc_g": 28.0,
        "fat_g": 10.0,
        "servings": 1,
        "instructions_text": (
            "1. Escurre el atún y los garbanzos.\n"
            "2. Mezcla con tomate cherry, cebolla morada y maíz.\n"
            "3. Aliña con limón, aceite y sal."
        ),
        "subcategory_name": "Ligera",
        "category_name": "Cena",
        "ingredients": [
            {"name": "Atún en lata (escurrido)", "quantity_g": 120, "kcal_100g": 116, "prot_100g": 25.5, "hc_100g": 0.0, "fat_100g": 1.0},
            {"name": "Garbanzos cocidos", "quantity_g": 100, "kcal_100g": 164, "prot_100g": 8.9, "hc_100g": 27.0, "fat_100g": 2.6},
            {"name": "Tomate cherry", "quantity_g": 80, "kcal_100g": 18, "prot_100g": 0.9, "hc_100g": 3.9, "fat_100g": 0.2},
            {"name": "Aceite de oliva", "quantity_g": 10, "kcal_100g": 884, "prot_100g": 0.0, "hc_100g": 0.0, "fat_100g": 100.0},
        ],
    },
]


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------

def seed_categories(session) -> dict[str, SubCategory]:
    """Insert default categories and subcategories.

    Returns:
        A mapping of 'CategoryName/SubcategoryName' → SubCategory instance
        so recipes can look up their subcategory by name.
    """
    subcat_map: dict[str, SubCategory] = {}
    for cat_data in CATEGORIES:
        category = Category(name=cat_data["name"], color=cat_data["color"])
        session.add(category)
        session.flush()  # get category.id

        for sub_name in cat_data["subcategories"]:
            subcat = SubCategory(name=sub_name, category_id=category.id)
            session.add(subcat)
            session.flush()
            subcat_map[f"{cat_data['name']}/{sub_name}"] = subcat

    print(f"  [OK] {len(CATEGORIES)} categorias y subcategorias insertadas")
    return subcat_map


def seed_profile(session) -> None:
    """Insert the default user profile (id=1)."""
    profile = Profile(
        id=1,
        weight_kg=75,
        height_cm=175,
        age=30,
        gender="male",
        activity_level=ActivityLevel.MODERATE,
        goal=Goal.MAINTAIN,
        kcal_target=2318,
        prot_pct=30,
        hc_pct=45,
        fat_pct=25,
        prot_g_target=174,
        hc_g_target=261,
        fat_g_target=64,
    )
    session.add(profile)
    print("  [OK] Perfil por defecto insertado")


def seed_extras(session) -> None:
    """Insert sample reusable extras."""
    for extra_data in EXTRAS:
        session.add(Extra(**extra_data))
    print(f"  [OK] {len(EXTRAS)} extras insertados")


def seed_recipes(session, subcat_map: dict[str, SubCategory]) -> None:
    """Insert sample recipes with their ingredients."""
    for recipe_data in RECIPES:
        key = f"{recipe_data['category_name']}/{recipe_data['subcategory_name']}"
        subcat = subcat_map.get(key)

        recipe = Recipe(
            name=recipe_data["name"],
            subcategory_id=subcat.id if subcat else None,
            instructions_text=recipe_data["instructions_text"],
            servings=recipe_data["servings"],
            kcal=recipe_data["kcal"],
            prot_g=recipe_data["prot_g"],
            hc_g=recipe_data["hc_g"],
            fat_g=recipe_data["fat_g"],
        )
        session.add(recipe)
        session.flush()  # get recipe.id

        for ing_data in recipe_data["ingredients"]:
            ingredient = RecipeIngredient(
                recipe_id=recipe.id,
                name=ing_data["name"],
                quantity_g=ing_data["quantity_g"],
                kcal_100g=ing_data["kcal_100g"],
                prot_100g=ing_data["prot_100g"],
                hc_100g=ing_data["hc_100g"],
                fat_100g=ing_data["fat_100g"],
            )
            session.add(ingredient)

    print(f"  [OK] {len(RECIPES)} recetas de ejemplo insertadas")


def run_seed() -> None:
    """Create tables and populate them with initial data."""
    print("Creando tablas...")
    create_db_and_tables()

    print("Insertando datos iniciales...")
    with get_session() as session:
        seed_categories_result = seed_categories(session)
        seed_profile(session)
        seed_extras(session)
        seed_recipes(session, seed_categories_result)
        session.commit()

    print("\n[DONE] Seed completado. Base de datos lista.")


if __name__ == "__main__":
    run_seed()
