"""Pure macro-gram calculation logic — no FastAPI or SQLModel dependencies.

Caloric density constants:
- Protein:      4 kcal / g
- Carbohydrates: 4 kcal / g
- Fat:           9 kcal / g
"""

from dataclasses import dataclass


@dataclass
class MacroGrams:
    """Daily macro targets expressed in grams."""

    prot_g: float
    hc_g: float
    fat_g: float


def calculate_macro_grams(
    kcal_target: float,
    prot_pct: float,
    hc_pct: float,
    fat_pct: float,
) -> MacroGrams:
    """Convert a calorie target + macro percentages into gram targets.

    Args:
        kcal_target: Daily calorie target in kcal.
        prot_pct: Percentage of calories from protein (0-100).
        hc_pct: Percentage of calories from carbohydrates (0-100).
        fat_pct: Percentage of calories from fat (0-100).

    Returns:
        MacroGrams with prot_g, hc_g, fat_g rounded to 1 decimal place.
    """
    prot_g = round((kcal_target * prot_pct / 100) / 4, 1)
    hc_g = round((kcal_target * hc_pct / 100) / 4, 1)
    fat_g = round((kcal_target * fat_pct / 100) / 9, 1)
    return MacroGrams(prot_g=prot_g, hc_g=hc_g, fat_g=fat_g)
