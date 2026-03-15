"""FastAPI router for MenuWeek, MenuDay and MenuSlot endpoints.

All routes are prefixed with /menu and tagged "menu" in Swagger.
"""

from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.backend.database import get_session
from app.backend.models.menu import MenuDay, MenuSlot, MenuWeek, SlotType
from app.backend.models.profile import Profile
from app.backend.models.recipe import Recipe
from app.backend.schemas.menu import (
    DayExtraRead,
    DayMacrosSummary,
    MenuDayRead,
    MenuWeekCreate,
    MenuWeekRead,
    MenuWeekSummary,
    SlotRead,
    SlotUpdate,
)
from app.backend.schemas.recipe import RecipeSummary
from app.backend.services.macro_calculator import MacroTotals
from app.core.menu_generator import autofill_week

router = APIRouter(prefix="/menu", tags=["menu"])

# Canonical slot ordering for consistent API responses
_SLOT_ORDER = [
    SlotType.DESAYUNO,
    SlotType.MEDIA_MANANA,
    SlotType.COMIDA,
    SlotType.MERIENDA,
    SlotType.CENA,
]


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _compute_day_macros(day: MenuDay) -> DayMacrosSummary:
    """Sum macro contributions from slots and extras for a single day."""
    kcal = prot_g = hc_g = fat_g = 0.0

    for slot in day.slots:
        if slot.recipe is not None:
            kcal += slot.recipe.kcal
            prot_g += slot.recipe.prot_g
            hc_g += slot.recipe.hc_g
            fat_g += slot.recipe.fat_g

    for de in day.day_extras:
        kcal += de.extra.kcal * de.quantity
        prot_g += de.extra.prot_g * de.quantity
        hc_g += de.extra.hc_g * de.quantity
        fat_g += de.extra.fat_g * de.quantity

    return DayMacrosSummary(
        kcal=round(kcal, 1),
        prot_g=round(prot_g, 1),
        hc_g=round(hc_g, 1),
        fat_g=round(fat_g, 1),
    )


def _build_slot_read(slot: MenuSlot) -> SlotRead:
    """Convert a MenuSlot ORM instance to SlotRead."""
    recipe_summary = (
        RecipeSummary.model_validate(slot.recipe) if slot.recipe is not None else None
    )
    return SlotRead(id=slot.id, slot_type=slot.slot_type, recipe=recipe_summary)


def _build_menu_week_read(week: MenuWeek) -> MenuWeekRead:
    """Build a full MenuWeekRead from a loaded MenuWeek ORM instance."""
    days_read: list[MenuDayRead] = []

    for day in sorted(week.days, key=lambda d: d.day_date):
        sorted_slots = sorted(
            day.slots, key=lambda s: _SLOT_ORDER.index(s.slot_type)
        )
        slots_read = [_build_slot_read(s) for s in sorted_slots]

        extras_read = [
            DayExtraRead(
                id=de.id,
                extra_id=de.extra_id,
                name=de.extra.name,
                quantity=de.quantity,
                kcal=round(de.extra.kcal * de.quantity, 1),
                prot_g=round(de.extra.prot_g * de.quantity, 1),
                hc_g=round(de.extra.hc_g * de.quantity, 1),
                fat_g=round(de.extra.fat_g * de.quantity, 1),
            )
            for de in day.day_extras
        ]

        days_read.append(
            MenuDayRead(
                id=day.id,
                day_date=day.day_date,
                slots=slots_read,
                day_extras=extras_read,
                macros=_compute_day_macros(day),
            )
        )

    return MenuWeekRead(
        id=week.id,
        week_start=week.week_start,
        label=week.label,
        days=days_read,
    )


def _load_week_relationships(week: MenuWeek) -> None:
    """Touch all lazy-loaded relationships while the session is still open."""
    for day in week.days:
        for slot in day.slots:
            _ = slot.recipe  # noqa: F841 — triggers lazy load
        for de in day.day_extras:
            _ = de.extra  # noqa: F841


# ---------------------------------------------------------------------------
# GET /menu/weeks
# ---------------------------------------------------------------------------


@router.get("/weeks", response_model=list[MenuWeekSummary], summary="Listar semanas")
def list_weeks() -> list[MenuWeekSummary]:
    """Return all stored weeks with a filled/total slots summary.

    Returns:
        List of :class:`MenuWeekSummary` sorted by week_start ascending.
    """
    with get_session() as session:
        weeks = session.exec(select(MenuWeek).order_by(MenuWeek.week_start)).all()  # type: ignore[arg-type]
        result: list[MenuWeekSummary] = []
        for week in weeks:
            filled = total = 0
            for day in week.days:
                for slot in day.slots:
                    total += 1
                    if slot.recipe_id is not None:
                        filled += 1
            result.append(
                MenuWeekSummary(
                    id=week.id,
                    week_start=week.week_start,
                    label=week.label,
                    filled_slots=filled,
                    total_slots=total,
                )
            )
        return result


# ---------------------------------------------------------------------------
# GET /menu/week/{week_start}
# ---------------------------------------------------------------------------


@router.get(
    "/week/{week_start}",
    response_model=MenuWeekRead,
    summary="Semana completa con macros",
)
def get_week(week_start: date) -> MenuWeekRead:
    """Return a full week including all slots, extras and per-day macro totals.

    Args:
        week_start: The Monday that identifies the week (YYYY-MM-DD).

    Raises:
        HTTPException 404: If no week exists for that date.
    """
    with get_session() as session:
        week = session.exec(
            select(MenuWeek).where(MenuWeek.week_start == week_start)
        ).first()
        if week is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe ninguna semana para {week_start}",
            )
        _load_week_relationships(week)
        return _build_menu_week_read(week)


# ---------------------------------------------------------------------------
# POST /menu/week
# ---------------------------------------------------------------------------


@router.post(
    "/week",
    response_model=MenuWeekRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear nueva semana",
)
def create_week(payload: MenuWeekCreate) -> MenuWeekRead:
    """Create a new MenuWeek with 5 days (Mon–Fri) and 5 slots per day.

    Args:
        payload: :class:`MenuWeekCreate` with ``week_start`` (must be Monday)
                 and an optional ``label``.

    Raises:
        HTTPException 400: If ``week_start`` is not a Monday.
        HTTPException 409: If a week already exists for that date.
    """
    if payload.week_start.weekday() != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="week_start debe ser lunes (weekday=0)",
        )

    with get_session() as session:
        existing = session.exec(
            select(MenuWeek).where(MenuWeek.week_start == payload.week_start)
        ).first()
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe una semana para {payload.week_start}",
            )

        week = MenuWeek(week_start=payload.week_start, label=payload.label)
        session.add(week)
        session.flush()  # assign week.id

        for day_offset in range(5):
            day = MenuDay(
                week_id=week.id,  # type: ignore[arg-type]
                day_date=payload.week_start + timedelta(days=day_offset),
            )
            session.add(day)
            session.flush()  # assign day.id

            for slot_type in _SLOT_ORDER:
                slot = MenuSlot(
                    day_id=day.id,  # type: ignore[arg-type]
                    slot_type=slot_type,
                )
                session.add(slot)

        session.commit()
        session.refresh(week)
        _load_week_relationships(week)
        return _build_menu_week_read(week)


# ---------------------------------------------------------------------------
# PUT /menu/slot/{slot_id}
# ---------------------------------------------------------------------------


@router.put(
    "/slot/{slot_id}",
    response_model=SlotRead,
    summary="Asignar receta a un slot",
)
def update_slot(slot_id: int, payload: SlotUpdate) -> SlotRead:
    """Assign or clear the recipe for a menu slot.

    Passing ``recipe_id: null`` empties the slot.

    Args:
        slot_id: Primary key of the :class:`MenuSlot` to update.
        payload: :class:`SlotUpdate` with the new ``recipe_id`` (or null).

    Raises:
        HTTPException 404: If the slot or the recipe does not exist.
    """
    with get_session() as session:
        slot = session.get(MenuSlot, slot_id)
        if slot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Slot con id={slot_id} no encontrado",
            )

        if payload.recipe_id is not None:
            recipe = session.get(Recipe, payload.recipe_id)
            if recipe is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Receta con id={payload.recipe_id} no encontrada",
                )

        slot.recipe_id = payload.recipe_id
        session.add(slot)
        session.commit()
        session.refresh(slot)

        recipe_summary: RecipeSummary | None = None
        if slot.recipe_id is not None:
            recipe = session.get(Recipe, slot.recipe_id)
            if recipe is not None:
                recipe_summary = RecipeSummary.model_validate(recipe)

        return SlotRead(id=slot.id, slot_type=slot.slot_type, recipe=recipe_summary)


# ---------------------------------------------------------------------------
# DELETE /menu/slot/{slot_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/slot/{slot_id}",
    response_model=SlotRead,
    summary="Vaciar un slot",
)
def clear_slot(slot_id: int) -> SlotRead:
    """Remove the recipe from a menu slot (alias for PUT with recipe_id=null).

    Args:
        slot_id: Primary key of the :class:`MenuSlot` to clear.

    Raises:
        HTTPException 404: If the slot does not exist.
    """
    with get_session() as session:
        slot = session.get(MenuSlot, slot_id)
        if slot is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Slot con id={slot_id} no encontrado",
            )
        slot.recipe_id = None
        session.add(slot)
        session.commit()
        return SlotRead(id=slot.id, slot_type=slot.slot_type, recipe=None)


# ---------------------------------------------------------------------------
# POST /menu/week/{week_start}/autofill
# ---------------------------------------------------------------------------


@router.post(
    "/week/{week_start}/autofill",
    response_model=MenuWeekRead,
    summary="Rellenar huecos automáticamente",
)
def autofill_menu(week_start: date) -> MenuWeekRead:
    """Fill all empty slots in the given week using the intelligent generator.

    Only empty slots are modified.  The algorithm respects the user's daily
    macro target (read from :class:`Profile` id=1) and picks recipes that fit
    within the remaining budget for each slot.

    Args:
        week_start: The Monday identifying the week to autofill.

    Raises:
        HTTPException 404: If the week or user profile does not exist.
    """
    with get_session() as session:
        week = session.exec(
            select(MenuWeek).where(MenuWeek.week_start == week_start)
        ).first()
        if week is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe ninguna semana para {week_start}",
            )

        # Fully load week relationships before passing to pure logic
        _load_week_relationships(week)

        # Load all recipes with their subcategory → category chain
        recipes = session.exec(select(Recipe)).all()
        for recipe in recipes:
            if recipe.subcategory is not None:
                _ = recipe.subcategory.category  # noqa: F841

        # Get macro targets from the stored profile
        profile = session.get(Profile, 1)
        if profile is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil no encontrado. Ejecuta el seed primero.",
            )

        target = MacroTotals(
            kcal=profile.kcal_target,
            prot_g=profile.prot_g_target,
            hc_g=profile.hc_g_target,
            fat_g=profile.fat_g_target,
        )

        assignments = autofill_week(week, list(recipes), target)

        for assignment in assignments:
            if assignment.recipe_id is not None:
                slot = session.get(MenuSlot, assignment.slot_id)
                if slot is not None:
                    slot.recipe_id = assignment.recipe_id
                    session.add(slot)

        session.commit()
        session.refresh(week)
        _load_week_relationships(week)
        return _build_menu_week_read(week)
