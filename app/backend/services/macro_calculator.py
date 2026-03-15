"""Macro calculator service.

Computes aggregate macro-nutrient totals for a recipe by summing the
proportional contribution of each ingredient.
"""

from dataclasses import dataclass

from app.backend.models.recipe import RecipeIngredient


@dataclass
class MacroTotals:
    """Aggregated macro-nutrient values for a recipe."""

    kcal: float
    prot_g: float
    hc_g: float
    fat_g: float


def calculate_recipe_macros(ingredients: list[RecipeIngredient]) -> MacroTotals:
    """Sum macro contributions from all ingredients in a recipe.

    For each ingredient the formula is:
        macro = (quantity_g / 100) * macro_100g

    Args:
        ingredients: List of :class:`RecipeIngredient` rows with per-100g
                     macro values already populated (e.g. by USDA).

    Returns:
        A :class:`MacroTotals` with the rounded totals for the whole recipe.
    """
    kcal = sum((ing.quantity_g / 100) * ing.kcal_100g for ing in ingredients)
    prot_g = sum((ing.quantity_g / 100) * ing.prot_100g for ing in ingredients)
    hc_g = sum((ing.quantity_g / 100) * ing.hc_100g for ing in ingredients)
    fat_g = sum((ing.quantity_g / 100) * ing.fat_100g for ing in ingredients)

    return MacroTotals(
        kcal=round(kcal, 1),
        prot_g=round(prot_g, 1),
        hc_g=round(hc_g, 1),
        fat_g=round(fat_g, 1),
    )
