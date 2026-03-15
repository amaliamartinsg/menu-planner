"""Basic unit tests for app.core.menu_generator.

These tests use lightweight MagicMock objects so no database is required.
"""

from unittest.mock import MagicMock

import pytest

from app.backend.models.menu import SlotType
from app.backend.services.macro_calculator import MacroTotals
from app.core.menu_generator import (
    SlotAssignment,
    autofill_week,
    filter_compatible_recipes,
    get_slot_macro_budget,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _recipe(id: int, kcal: float, category_name: str) -> MagicMock:
    """Return a minimal mock Recipe with the given kcal and category."""
    r = MagicMock()
    r.id = id
    r.kcal = kcal
    r.prot_g = 10.0
    r.hc_g = 20.0
    r.fat_g = 5.0
    r.subcategory = MagicMock()
    r.subcategory.category = MagicMock()
    r.subcategory.category.name = category_name
    return r


def _recipe_no_subcat(id: int, kcal: float) -> MagicMock:
    """Return a mock Recipe with no subcategory."""
    r = MagicMock()
    r.id = id
    r.kcal = kcal
    r.prot_g = 10.0
    r.hc_g = 20.0
    r.fat_g = 5.0
    r.subcategory = None
    return r


# ---------------------------------------------------------------------------
# get_slot_macro_budget
# ---------------------------------------------------------------------------


def test_budget_basic_subtraction() -> None:
    consumed = MacroTotals(kcal=500.0, prot_g=30.0, hc_g=60.0, fat_g=20.0)
    target = MacroTotals(kcal=2000.0, prot_g=150.0, hc_g=225.0, fat_g=56.0)
    budget = get_slot_macro_budget(consumed, SlotType.COMIDA, target)
    assert budget.kcal == 1500.0
    assert budget.prot_g == 120.0
    assert budget.hc_g == 165.0
    assert budget.fat_g == 36.0


def test_budget_floors_at_zero() -> None:
    consumed = MacroTotals(kcal=2500.0, prot_g=200.0, hc_g=300.0, fat_g=80.0)
    target = MacroTotals(kcal=2000.0, prot_g=150.0, hc_g=225.0, fat_g=56.0)
    budget = get_slot_macro_budget(consumed, SlotType.CENA, target)
    assert budget.kcal == 0.0
    assert budget.prot_g == 0.0
    assert budget.hc_g == 0.0
    assert budget.fat_g == 0.0


def test_budget_slot_type_ignored_in_mvp() -> None:
    """Different slot types must yield the same budget (MVP simplification)."""
    consumed = MacroTotals(kcal=400.0, prot_g=20.0, hc_g=50.0, fat_g=10.0)
    target = MacroTotals(kcal=2000.0, prot_g=150.0, hc_g=225.0, fat_g=56.0)
    b1 = get_slot_macro_budget(consumed, SlotType.DESAYUNO, target)
    b2 = get_slot_macro_budget(consumed, SlotType.CENA, target)
    assert b1 == b2


# ---------------------------------------------------------------------------
# filter_compatible_recipes
# ---------------------------------------------------------------------------


def test_filter_returns_only_matching_category() -> None:
    r1 = _recipe(1, 300.0, "desayuno")
    r2 = _recipe(2, 400.0, "comida")
    r3 = _recipe(3, 200.0, "desayuno")
    budget = MacroTotals(kcal=500.0, prot_g=50.0, hc_g=100.0, fat_g=30.0)
    result = filter_compatible_recipes([r1, r2, r3], SlotType.DESAYUNO, budget)
    ids = {r.id for r in result}
    assert ids == {1, 3}


def test_filter_excludes_over_budget() -> None:
    r1 = _recipe(1, 300.0, "comida")
    r2 = _recipe(2, 600.0, "comida")
    budget = MacroTotals(kcal=400.0, prot_g=50.0, hc_g=100.0, fat_g=30.0)
    result = filter_compatible_recipes([r1, r2], SlotType.COMIDA, budget)
    assert len(result) == 1
    assert result[0].id == 1


def test_filter_excludes_recipes_without_subcategory() -> None:
    r1 = _recipe(1, 300.0, "desayuno")
    r2 = _recipe_no_subcat(2, 200.0)
    budget = MacroTotals(kcal=500.0, prot_g=50.0, hc_g=100.0, fat_g=30.0)
    result = filter_compatible_recipes([r1, r2], SlotType.DESAYUNO, budget)
    assert len(result) == 1
    assert result[0].id == 1


def test_filter_sorted_by_kcal_ascending() -> None:
    r1 = _recipe(1, 400.0, "cena")
    r2 = _recipe(2, 200.0, "cena")
    r3 = _recipe(3, 300.0, "cena")
    budget = MacroTotals(kcal=500.0, prot_g=50.0, hc_g=100.0, fat_g=30.0)
    result = filter_compatible_recipes([r1, r2, r3], SlotType.CENA, budget)
    assert [r.id for r in result] == [2, 3, 1]


def test_filter_snack_slots_use_snack_category() -> None:
    r1 = _recipe(1, 150.0, "snack")
    r2 = _recipe(2, 150.0, "comida")
    budget = MacroTotals(kcal=500.0, prot_g=50.0, hc_g=100.0, fat_g=30.0)

    result_mm = filter_compatible_recipes([r1, r2], SlotType.MEDIA_MANANA, budget)
    assert len(result_mm) == 1 and result_mm[0].id == 1

    result_mer = filter_compatible_recipes([r1, r2], SlotType.MERIENDA, budget)
    assert len(result_mer) == 1 and result_mer[0].id == 1


# ---------------------------------------------------------------------------
# autofill_week
# ---------------------------------------------------------------------------


def _make_week(slots_data: list[tuple[int, SlotType, int | None]]) -> MagicMock:
    """Build a mock MenuWeek from a list of (slot_id, slot_type, recipe_id)."""
    slots = []
    for slot_id, slot_type, recipe_id in slots_data:
        slot = MagicMock()
        slot.id = slot_id
        slot.slot_type = slot_type
        slot.recipe_id = recipe_id
        slot.recipe = None  # no actual recipe loaded for filled slots in this test
        slots.append(slot)

    day = MagicMock()
    day.slots = slots
    day.day_extras = []

    week = MagicMock()
    week.days = [day]
    return week


def test_autofill_fills_empty_slots() -> None:
    week = _make_week(
        [
            (1, SlotType.DESAYUNO, None),
            (2, SlotType.MEDIA_MANANA, None),
        ]
    )
    recipes = [
        _recipe(10, 300.0, "desayuno"),
        _recipe(20, 150.0, "snack"),
    ]
    target = MacroTotals(kcal=2000.0, prot_g=150.0, hc_g=225.0, fat_g=56.0)
    assignments = autofill_week(week, recipes, target)
    assert len(assignments) == 2
    slot_ids = {a.slot_id for a in assignments}
    assert slot_ids == {1, 2}


def test_autofill_skips_already_filled() -> None:
    week = _make_week(
        [
            (1, SlotType.DESAYUNO, 99),  # already filled
            (2, SlotType.COMIDA, None),
        ]
    )
    # slot 1 has recipe_id=99; its .recipe is MagicMock (non-None) for the test
    week.days[0].slots[0].recipe = MagicMock()
    week.days[0].slots[0].recipe.kcal = 300.0
    week.days[0].slots[0].recipe.prot_g = 25.0
    week.days[0].slots[0].recipe.hc_g = 40.0
    week.days[0].slots[0].recipe.fat_g = 10.0

    recipes = [_recipe(10, 400.0, "comida")]
    target = MacroTotals(kcal=2000.0, prot_g=150.0, hc_g=225.0, fat_g=56.0)
    assignments = autofill_week(week, recipes, target)
    assert len(assignments) == 1
    assert assignments[0].slot_id == 2


def test_autofill_returns_empty_when_no_recipes() -> None:
    week = _make_week([(1, SlotType.DESAYUNO, None)])
    recipes: list = []  # no recipes at all
    target = MacroTotals(kcal=2000.0, prot_g=150.0, hc_g=225.0, fat_g=56.0)
    assignments = autofill_week(week, recipes, target)
    assert assignments == []
