"""FastAPI router for Recipe endpoints.

All routes are prefixed with /recipes and tagged "recipes" in Swagger.

Route order matters for FastAPI's path matching:
  - /recipes/images  must come before /recipes/{id}
  - /recipes/suggest is a POST so there is no ambiguity
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import select

from app.backend.database import get_session
from app.backend.models.category import SubCategory
from app.backend.models.recipe import Recipe, RecipeIngredient
from app.backend.schemas.recipe import (
    RecipeCreate,
    RecipeRead,
    RecipeSuggestion,
    RecipeSummary,
    RecipeUpdate,
)
from app.backend.services.usda import USDAAuthError, get_nutrition
from app.backend.services.macro_calculator import calculate_recipe_macros
from app.backend.services.openai_service import OpenAIAuthError, suggest_recipe
from app.backend.services.unsplash import UnsplashAuthError, search_images

router = APIRouter(prefix="/recipes", tags=["recipes"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _build_recipe_read(recipe: Recipe) -> RecipeRead:
    """Convert a Recipe ORM instance to its RecipeRead schema."""
    return RecipeRead.model_validate(recipe)


# ---------------------------------------------------------------------------
# GET /recipes/images  — must be declared before GET /recipes/{id}
# ---------------------------------------------------------------------------


@router.get("/images", response_model=list[str], summary="Buscar imágenes en Unsplash")
async def get_recipe_images(
    query: Annotated[str, Query(min_length=1, description="Término de búsqueda")],
    count: Annotated[int, Query(ge=1, le=20)] = 5,
) -> list[str]:
    """Return a list of Unsplash image URLs matching *query*.

    Args:
        query: Search term (English terms give better results).
        count: Number of images to return (1-20, default 5).

    Raises:
        HTTPException 502: If Unsplash returns an error.
    """
    try:
        urls = await search_images(query=query, count=count)
    except UnsplashAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    return urls


# ---------------------------------------------------------------------------
# GET /recipes
# ---------------------------------------------------------------------------


@router.get("", response_model=list[RecipeSummary], summary="Listar recetas")
def list_recipes(
    category_id: Annotated[int | None, Query()] = None,
    subcategory_id: Annotated[int | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> list[RecipeSummary]:
    """Return a summarised list of recipes with optional filters.

    Args:
        category_id: Filter by top-level category (joins through SubCategory).
        subcategory_id: Filter by subcategory.
        search: Case-insensitive partial name match.
    """
    with get_session() as session:
        query = select(Recipe)

        if subcategory_id is not None:
            query = query.where(Recipe.subcategory_id == subcategory_id)
        elif category_id is not None:
            # Join through SubCategory to filter by parent category
            query = query.join(
                SubCategory, Recipe.subcategory_id == SubCategory.id, isouter=True
            ).where(SubCategory.category_id == category_id)

        if search:
            query = query.where(Recipe.name.ilike(f"%{search}%"))  # type: ignore[attr-defined]

        recipes = session.exec(query).all()
        return [RecipeSummary.model_validate(r) for r in recipes]


# ---------------------------------------------------------------------------
# GET /recipes/{id}
# ---------------------------------------------------------------------------


@router.get("/{recipe_id}", response_model=RecipeRead, summary="Detalle de receta")
def get_recipe(recipe_id: int) -> RecipeRead:
    """Return full recipe details including ingredients and macros.

    Raises:
        HTTPException 404: If the recipe does not exist.
    """
    with get_session() as session:
        recipe = session.get(Recipe, recipe_id)
        if recipe is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Receta con id={recipe_id} no encontrada",
            )
        # Access ingredients while session is open so the lazy load completes
        _ = recipe.ingredients
        return _build_recipe_read(recipe)


# ---------------------------------------------------------------------------
# POST /recipes
# ---------------------------------------------------------------------------


@router.post("", response_model=RecipeRead, status_code=status.HTTP_201_CREATED, summary="Crear receta")
async def create_recipe(payload: RecipeCreate) -> RecipeRead:
    """Create a new recipe, fetching macro data from USDA for each ingredient.

    Flow:
        1. For each ingredient, translate the name to English via GPT-4o mini,
           then query USDA FoodData Central for per-100g macro values.
        2. Persist :class:`RecipeIngredient` rows with those values.
        3. Compute recipe macro totals via :func:`calculate_recipe_macros`.
        4. Persist the :class:`Recipe` and return :class:`RecipeRead`.

    Raises:
        HTTPException 403: If the USDA API key is invalid.
        HTTPException 502: If the USDA API call fails unexpectedly.
    """
    ingredient_rows: list[RecipeIngredient] = []

    for ing_input in payload.ingredients:
        try:
            nutrition = await get_nutrition(ing_input.name)
        except USDAAuthError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            ) from exc
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=str(exc),
            ) from exc

        ingredient_rows.append(
            RecipeIngredient(
                name=ing_input.name,
                quantity_g=ing_input.quantity_g,
                kcal_100g=nutrition.kcal_100g,
                prot_100g=nutrition.prot_100g,
                hc_100g=nutrition.hc_100g,
                fat_100g=nutrition.fat_100g,
            )
        )

    totals = calculate_recipe_macros(ingredient_rows)

    recipe = Recipe(
        name=payload.name,
        subcategory_id=payload.subcategory_id,
        instructions_text=payload.instructions_text,
        image_url=payload.image_url,
        servings=payload.servings,
        kcal=totals.kcal,
        prot_g=totals.prot_g,
        hc_g=totals.hc_g,
        fat_g=totals.fat_g,
    )

    with get_session() as session:
        session.add(recipe)
        session.flush()  # assigns recipe.id before we set FKs

        for row in ingredient_rows:
            row.recipe_id = recipe.id  # type: ignore[assignment]
            session.add(row)

        session.commit()
        session.refresh(recipe)
        _ = recipe.ingredients  # load while session is still open
        return _build_recipe_read(recipe)


# ---------------------------------------------------------------------------
# PUT /recipes/{id}
# ---------------------------------------------------------------------------


@router.put("/{recipe_id}", response_model=RecipeRead, summary="Actualizar receta")
async def update_recipe(recipe_id: int, payload: RecipeUpdate) -> RecipeRead:
    """Update an existing recipe.

    If ``ingredients`` are provided the old ingredient rows are replaced and
    macros are recalculated via USDA. If ``ingredients`` is omitted, macros
    remain unchanged.

    Raises:
        HTTPException 404: If the recipe does not exist.
        HTTPException 403: If the USDA API key is invalid.
        HTTPException 502: If a USDA call fails.
    """
    with get_session() as session:
        recipe = session.get(Recipe, recipe_id)
        if recipe is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Receta con id={recipe_id} no encontrada",
            )

        # Update scalar fields if provided
        if payload.name is not None:
            recipe.name = payload.name
        if payload.subcategory_id is not None:
            recipe.subcategory_id = payload.subcategory_id
        if payload.instructions_text is not None:
            recipe.instructions_text = payload.instructions_text
        if payload.image_url is not None:
            recipe.image_url = payload.image_url
        if payload.servings is not None:
            recipe.servings = payload.servings

        if payload.ingredients is not None:
            # Delete old ingredient rows
            old_ingredients = session.exec(
                select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id)
            ).all()
            for old in old_ingredients:
                session.delete(old)
            session.flush()

            # Fetch macros for new ingredients
            new_rows: list[RecipeIngredient] = []
            for ing_input in payload.ingredients:
                try:
                    nutrition = await get_nutrition(ing_input.name)
                except RuntimeError as exc:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=str(exc),
                    ) from exc

                new_rows.append(
                    RecipeIngredient(
                        recipe_id=recipe_id,
                        name=ing_input.name,
                        quantity_g=ing_input.quantity_g,
                        kcal_100g=nutrition.kcal_100g,
                        prot_100g=nutrition.prot_100g,
                        hc_100g=nutrition.hc_100g,
                        fat_100g=nutrition.fat_100g,
                    )
                )

            totals = calculate_recipe_macros(new_rows)
            recipe.kcal = totals.kcal
            recipe.prot_g = totals.prot_g
            recipe.hc_g = totals.hc_g
            recipe.fat_g = totals.fat_g

            for row in new_rows:
                session.add(row)

        session.add(recipe)
        session.commit()
        session.refresh(recipe)
        _ = recipe.ingredients
        return _build_recipe_read(recipe)


# ---------------------------------------------------------------------------
# DELETE /recipes/{id}
# ---------------------------------------------------------------------------


@router.delete(
    "/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar receta",
)
def delete_recipe(recipe_id: int) -> None:
    """Delete a recipe and all its ingredient rows.

    Raises:
        HTTPException 404: If the recipe does not exist.
    """
    with get_session() as session:
        recipe = session.get(Recipe, recipe_id)
        if recipe is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Receta con id={recipe_id} no encontrada",
            )

        # Delete ingredients first (no CASCADE configured at DB level)
        ingredients = session.exec(
            select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe_id)
        ).all()
        for ing in ingredients:
            session.delete(ing)

        session.delete(recipe)
        session.commit()


# ---------------------------------------------------------------------------
# POST /recipes/suggest  — Despensa Virtual
# ---------------------------------------------------------------------------


@router.post(
    "/suggest",
    response_model=RecipeSuggestion,
    summary="Sugerir receta con IA (Despensa Virtual)",
)
async def suggest_recipe_endpoint(ingredients: list[str]) -> RecipeSuggestion:
    """Ask GPT-4o mini to suggest a recipe from the provided ingredients.

    The returned :class:`RecipeSuggestion` is a draft that the user reviews
    and edits before saving — it is **not** persisted automatically.

    Args:
        ingredients: List of ingredient names available in the pantry.

    Raises:
        HTTPException 400: If no ingredients are provided.
        HTTPException 502: If the OpenAI call fails or returns invalid JSON.
    """
    if not ingredients:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes proporcionar al menos un ingrediente",
        )

    try:
        suggestion = await suggest_recipe(ingredients)
    except OpenAIAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return suggestion
