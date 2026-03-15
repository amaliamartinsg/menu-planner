"""Unit tests for app.core.tdee and app.core.macro_targets."""

import pytest

from app.backend.models.profile import ActivityLevel, Goal
from app.core.macro_targets import MacroGrams, calculate_macro_grams
from app.core.tdee import apply_goal, calculate_bmr, calculate_tdee


# ---------------------------------------------------------------------------
# calculate_bmr
# ---------------------------------------------------------------------------


def test_bmr_male() -> None:
    # (10×75) + (6.25×175) - (5×30) + 5 = 750 + 1093.75 - 150 + 5 = 1698.75
    result = calculate_bmr(weight_kg=75, height_cm=175, age=30, gender="male")
    assert abs(result - 1698.75) < 0.01


def test_bmr_female() -> None:
    # (10×60) + (6.25×165) - (5×25) - 161 = 600 + 1031.25 - 125 - 161 = 1345.25
    result = calculate_bmr(weight_kg=60, height_cm=165, age=25, gender="female")
    assert abs(result - 1345.25) < 0.01


def test_bmr_invalid_gender() -> None:
    with pytest.raises(ValueError, match="male.*female"):
        calculate_bmr(weight_kg=70, height_cm=170, age=28, gender="other")


# ---------------------------------------------------------------------------
# calculate_tdee
# ---------------------------------------------------------------------------


def test_tdee_sedentary() -> None:
    bmr = 1700.0
    result = calculate_tdee(bmr, ActivityLevel.SEDENTARY)
    assert abs(result - 1700.0 * 1.2) < 0.01


def test_tdee_moderate() -> None:
    bmr = 1700.0
    result = calculate_tdee(bmr, ActivityLevel.MODERATE)
    assert abs(result - 1700.0 * 1.55) < 0.01


def test_tdee_very_active() -> None:
    bmr = 1700.0
    result = calculate_tdee(bmr, ActivityLevel.VERY_ACTIVE)
    assert abs(result - 1700.0 * 1.9) < 0.01


# ---------------------------------------------------------------------------
# apply_goal
# ---------------------------------------------------------------------------


def test_goal_maintain() -> None:
    assert apply_goal(2000.0, Goal.MAINTAIN) == 2000.0


def test_goal_deficit() -> None:
    assert apply_goal(2000.0, Goal.DEFICIT) == 1500.0


def test_goal_surplus() -> None:
    assert apply_goal(2000.0, Goal.SURPLUS) == 2300.0


def test_goal_floor_at_1000() -> None:
    """Very low TDEE + deficit must not go below safety floor of 1000 kcal."""
    result = apply_goal(1200.0, Goal.DEFICIT)  # 1200 - 500 = 700 → floored to 1000
    assert result == 1000.0


# ---------------------------------------------------------------------------
# calculate_macro_grams
# ---------------------------------------------------------------------------


def test_macro_grams_standard() -> None:
    # 2000 kcal, 30% prot, 45% hc, 25% fat
    result = calculate_macro_grams(2000.0, 30.0, 45.0, 25.0)
    assert isinstance(result, MacroGrams)
    assert abs(result.prot_g - 150.0) < 0.2   # (2000 * 0.30) / 4 = 150
    assert abs(result.hc_g - 225.0) < 0.2     # (2000 * 0.45) / 4 = 225
    assert abs(result.fat_g - 55.6) < 0.2     # (2000 * 0.25) / 9 ≈ 55.6


def test_macro_grams_equal_split() -> None:
    # 1800 kcal, 33/34/33 split
    result = calculate_macro_grams(1800.0, 33.0, 34.0, 33.0)
    assert result.prot_g == round((1800 * 0.33) / 4, 1)
    assert result.hc_g == round((1800 * 0.34) / 4, 1)
    assert result.fat_g == round((1800 * 0.33) / 9, 1)


def test_macro_grams_zero_pct() -> None:
    result = calculate_macro_grams(2000.0, 0.0, 100.0, 0.0)
    assert result.prot_g == 0.0
    assert result.fat_g == 0.0
    assert result.hc_g > 0
