"""Pure TDEE/BMR calculation logic — no FastAPI or SQLModel dependencies.

Formulas:
- BMR: Mifflin-St Jeor equation
- TDEE: BMR × activity multiplier
- kcal_target: TDEE adjusted for the user's goal
"""

from app.backend.models.profile import ActivityLevel, Goal

# ---------------------------------------------------------------------------
# Activity multipliers (Mifflin-St Jeor)
# ---------------------------------------------------------------------------

_ACTIVITY_MULTIPLIERS: dict[ActivityLevel, float] = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHT: 1.375,
    ActivityLevel.MODERATE: 1.55,
    ActivityLevel.ACTIVE: 1.725,
    ActivityLevel.VERY_ACTIVE: 1.9,
}

# ---------------------------------------------------------------------------
# Goal adjustments (kcal delta relative to TDEE)
# ---------------------------------------------------------------------------

_GOAL_DELTA: dict[Goal, float] = {
    Goal.DEFICIT: -500.0,
    Goal.MAINTAIN: 0.0,
    Goal.SURPLUS: +300.0,
}


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def calculate_bmr(
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: str,
) -> float:
    """Calculate Basal Metabolic Rate using the Mifflin-St Jeor equation.

    Args:
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimetres.
        age: Age in years.
        gender: Biological sex — 'male' or 'female'.

    Returns:
        BMR in kcal/day.

    Raises:
        ValueError: If gender is not 'male' or 'female'.
    """
    base = (10 * weight_kg) + (6.25 * height_cm) - (5 * age)
    if gender == "male":
        return base + 5.0
    elif gender == "female":
        return base - 161.0
    else:
        raise ValueError(f"Gender must be 'male' or 'female', got: {gender!r}")


def calculate_tdee(bmr: float, activity_level: ActivityLevel) -> float:
    """Multiply BMR by the activity factor to obtain Total Daily Energy Expenditure.

    Args:
        bmr: Basal Metabolic Rate in kcal/day.
        activity_level: Physical activity category.

    Returns:
        TDEE in kcal/day.
    """
    multiplier = _ACTIVITY_MULTIPLIERS[activity_level]
    return round(bmr * multiplier, 2)


def apply_goal(tdee: float, goal: Goal) -> float:
    """Adjust TDEE according to the user's caloric goal.

    Args:
        tdee: Total Daily Energy Expenditure in kcal/day.
        goal: Caloric goal (deficit / maintain / surplus).

    Returns:
        Daily calorie target in kcal. Always >= 1000 kcal (safety floor).
    """
    target = tdee + _GOAL_DELTA[goal]
    return max(target, 1000.0)
