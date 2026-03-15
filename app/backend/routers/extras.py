"""FastAPI router for Extra CRUD and MenuDayExtra endpoints.

Covers:
  /extras/*          — catalogue of reusable quick-add items
  /menu/day/*/extras — attach/detach extras from a specific day
"""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.backend.database import get_session
from app.backend.models.extra import Extra, MenuDayExtra
from app.backend.models.menu import MenuDay
from app.backend.schemas.extra import (
    ExtraCreate,
    ExtraRead,
    ExtraUpdate,
    MenuDayExtraCreate,
    MenuDayExtraRead,
)

router = APIRouter(tags=["extras"])


# ---------------------------------------------------------------------------
# GET /extras
# ---------------------------------------------------------------------------


@router.get("/extras", response_model=list[ExtraRead], summary="Listar extras")
def list_extras() -> list[ExtraRead]:
    """Return all predefined extra items sorted by name."""
    with get_session() as session:
        extras = session.exec(select(Extra).order_by(Extra.name)).all()  # type: ignore[arg-type]
        return [ExtraRead.model_validate(e) for e in extras]


# ---------------------------------------------------------------------------
# POST /extras
# ---------------------------------------------------------------------------


@router.post(
    "/extras",
    response_model=ExtraRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear extra",
)
def create_extra(payload: ExtraCreate) -> ExtraRead:
    """Create a new reusable extra item.

    Args:
        payload: :class:`ExtraCreate` with name and macro values.

    Returns:
        The created :class:`ExtraRead`.
    """
    with get_session() as session:
        extra = Extra(
            name=payload.name,
            kcal=payload.kcal,
            prot_g=payload.prot_g,
            hc_g=payload.hc_g,
            fat_g=payload.fat_g,
        )
        session.add(extra)
        session.commit()
        session.refresh(extra)
        return ExtraRead.model_validate(extra)


# ---------------------------------------------------------------------------
# PUT /extras/{extra_id}
# ---------------------------------------------------------------------------


@router.put("/extras/{extra_id}", response_model=ExtraRead, summary="Actualizar extra")
def update_extra(extra_id: int, payload: ExtraUpdate) -> ExtraRead:
    """Partially update an extra item.

    Only provided fields are updated; omitted fields remain unchanged.

    Args:
        extra_id: Primary key of the :class:`Extra` to update.
        payload: :class:`ExtraUpdate` with the fields to change.

    Raises:
        HTTPException 404: If the extra does not exist.
    """
    with get_session() as session:
        extra = session.get(Extra, extra_id)
        if extra is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extra con id={extra_id} no encontrado",
            )

        if payload.name is not None:
            extra.name = payload.name
        if payload.kcal is not None:
            extra.kcal = payload.kcal
        if payload.prot_g is not None:
            extra.prot_g = payload.prot_g
        if payload.hc_g is not None:
            extra.hc_g = payload.hc_g
        if payload.fat_g is not None:
            extra.fat_g = payload.fat_g

        session.add(extra)
        session.commit()
        session.refresh(extra)
        return ExtraRead.model_validate(extra)


# ---------------------------------------------------------------------------
# DELETE /extras/{extra_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/extras/{extra_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar extra",
)
def delete_extra(extra_id: int) -> None:
    """Delete a predefined extra item.

    Args:
        extra_id: Primary key of the :class:`Extra` to delete.

    Raises:
        HTTPException 404: If the extra does not exist.
    """
    with get_session() as session:
        extra = session.get(Extra, extra_id)
        if extra is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extra con id={extra_id} no encontrado",
            )
        session.delete(extra)
        session.commit()


# ---------------------------------------------------------------------------
# POST /menu/day/{day_id}/extras
# ---------------------------------------------------------------------------


@router.post(
    "/menu/day/{day_id}/extras",
    response_model=MenuDayExtraRead,
    status_code=status.HTTP_201_CREATED,
    summary="Añadir extra a un día",
)
def add_day_extra(day_id: int, payload: MenuDayExtraCreate) -> MenuDayExtraRead:
    """Attach a predefined extra to a menu day with a quantity multiplier.

    Args:
        day_id: Primary key of the :class:`MenuDay`.
        payload: :class:`MenuDayExtraCreate` with ``extra_id`` and ``quantity``.

    Raises:
        HTTPException 404: If the day or the extra does not exist.
    """
    with get_session() as session:
        day = session.get(MenuDay, day_id)
        if day is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Día con id={day_id} no encontrado",
            )

        extra = session.get(Extra, payload.extra_id)
        if extra is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Extra con id={payload.extra_id} no encontrado",
            )

        day_extra = MenuDayExtra(
            day_id=day_id,
            extra_id=payload.extra_id,
            quantity=payload.quantity,
        )
        session.add(day_extra)
        session.commit()
        session.refresh(day_extra)
        _ = day_extra.extra  # trigger lazy load while session is open
        return MenuDayExtraRead.model_validate(day_extra)


# ---------------------------------------------------------------------------
# DELETE /menu/day-extra/{day_extra_id}
# ---------------------------------------------------------------------------


@router.delete(
    "/menu/day-extra/{day_extra_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Quitar extra de un día",
)
def remove_day_extra(day_extra_id: int) -> None:
    """Remove a :class:`MenuDayExtra` association from a menu day.

    Args:
        day_extra_id: Primary key of the :class:`MenuDayExtra` to delete.

    Raises:
        HTTPException 404: If the association does not exist.
    """
    with get_session() as session:
        day_extra = session.get(MenuDayExtra, day_extra_id)
        if day_extra is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"MenuDayExtra con id={day_extra_id} no encontrado",
            )
        session.delete(day_extra)
        session.commit()
