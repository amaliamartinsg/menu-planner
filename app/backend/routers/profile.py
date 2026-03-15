"""FastAPI router for the user Profile endpoints.

Endpoints:
    GET  /profile                — Return the current profile with all computed targets.
    PUT  /profile                — Update profile, recalculate TDEE and macro targets.
    POST /profile/calculate-tdee — Preview TDEE without writing to the database.
"""

from fastapi import APIRouter, HTTPException

from app.backend.database import get_session
from app.backend.models.profile import ActivityLevel, Goal, Profile
from app.backend.schemas.profile import ProfileRead, ProfileUpdate, TDEEPreview
from app.core.macro_targets import calculate_macro_grams
from app.core.tdee import apply_goal, calculate_bmr, calculate_tdee
from sqlmodel import select

router = APIRouter(prefix="/profile", tags=["profile"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_or_create_profile(session) -> Profile:  # type: ignore[no-untyped-def]
    """Return the single Profile row (id=1), creating it if it doesn't exist yet."""
    profile = session.get(Profile, 1)
    if profile is None:
        profile = Profile()
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


def _recalculate_and_store(profile: Profile) -> None:
    """Recompute kcal_target and macro gram targets directly on the profile object.

    This mutates *profile* in place; the caller is responsible for committing.
    """
    bmr = calculate_bmr(profile.weight_kg, profile.height_cm, profile.age, profile.gender)
    tdee = calculate_tdee(bmr, profile.activity_level)
    kcal_target = apply_goal(tdee, profile.goal)
    macros = calculate_macro_grams(kcal_target, profile.prot_pct, profile.hc_pct, profile.fat_pct)

    profile.kcal_target = kcal_target
    profile.prot_g_target = macros.prot_g
    profile.hc_g_target = macros.hc_g
    profile.fat_g_target = macros.fat_g


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=ProfileRead)
def get_profile() -> ProfileRead:
    """Devolver el perfil actual con todos los targets calculados."""
    with get_session() as session:
        profile = _get_or_create_profile(session)
        return ProfileRead.model_validate(profile)


@router.put("", response_model=ProfileRead)
def update_profile(payload: ProfileUpdate) -> ProfileRead:
    """Actualizar el perfil, recalcular TDEE y guardar macro targets en BD."""
    with get_session() as session:
        profile = _get_or_create_profile(session)

        update_data = payload.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(profile, field, value)

        _recalculate_and_store(profile)

        session.add(profile)
        session.commit()
        session.refresh(profile)
        return ProfileRead.model_validate(profile)


@router.post("/calculate-tdee", response_model=TDEEPreview)
def preview_tdee(payload: ProfileUpdate) -> TDEEPreview:
    """Calcular TDEE de forma preview sin escribir en la base de datos.

    Toma el perfil actual de BD y aplica encima los campos que vengan en el
    payload para que la UI pueda mostrar los resultados en tiempo real.
    """
    with get_session() as session:
        profile = _get_or_create_profile(session)

        # Merge payload over the stored profile values (without persisting)
        update_data = payload.model_dump(exclude_none=True)
        weight_kg: float = update_data.get("weight_kg", profile.weight_kg)
        height_cm: float = update_data.get("height_cm", profile.height_cm)
        age: int = update_data.get("age", profile.age)
        gender: str = update_data.get("gender", profile.gender)
        activity_level: ActivityLevel = update_data.get("activity_level", profile.activity_level)
        goal: Goal = update_data.get("goal", profile.goal)
        prot_pct: float = update_data.get("prot_pct", profile.prot_pct)
        hc_pct: float = update_data.get("hc_pct", profile.hc_pct)
        fat_pct: float = update_data.get("fat_pct", profile.fat_pct)

    try:
        bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    tdee = calculate_tdee(bmr, activity_level)
    kcal_target = apply_goal(tdee, goal)
    macros = calculate_macro_grams(kcal_target, prot_pct, hc_pct, fat_pct)

    return TDEEPreview(
        bmr=round(bmr, 2),
        tdee=round(tdee, 2),
        kcal_target=kcal_target,
        prot_g_target=macros.prot_g,
        hc_g_target=macros.hc_g,
        fat_g_target=macros.fat_g,
    )
