"""FastAPI router for Category and SubCategory endpoints.

All routes are tagged "categories" in Swagger.
"""

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.backend.database import get_session
from app.backend.models.category import Category, SubCategory
from app.backend.schemas.category import (
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    SubCategoryCreate,
    SubCategoryRead,
    SubCategoryUpdate,
)

router = APIRouter(tags=["categories"])


# ---------------------------------------------------------------------------
# Category CRUD
# ---------------------------------------------------------------------------


@router.get("/categories", response_model=list[CategoryRead], summary="Listar categorías")
def list_categories() -> list[CategoryRead]:
    """Return all categories with their nested subcategories."""
    with get_session() as session:
        categories = session.exec(select(Category)).all()
        # Access subcategories while session is open
        result = []
        for cat in categories:
            _ = cat.subcategories
            result.append(CategoryRead.model_validate(cat))
        return result


@router.post(
    "/categories",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear categoría",
)
def create_category(payload: CategoryCreate) -> CategoryRead:
    """Create a new top-level category."""
    with get_session() as session:
        category = Category(name=payload.name, color=payload.color)
        session.add(category)
        session.commit()
        session.refresh(category)
        _ = category.subcategories
        return CategoryRead.model_validate(category)


@router.put("/categories/{category_id}", response_model=CategoryRead, summary="Editar categoría")
def update_category(category_id: int, payload: CategoryUpdate) -> CategoryRead:
    """Update name and/or color of an existing category.

    Raises:
        HTTPException 404: If the category does not exist.
    """
    with get_session() as session:
        category = session.get(Category, category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoría con id={category_id} no encontrada",
            )
        if payload.name is not None:
            category.name = payload.name
        if payload.color is not None:
            category.color = payload.color

        session.add(category)
        session.commit()
        session.refresh(category)
        _ = category.subcategories
        return CategoryRead.model_validate(category)


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar categoría",
)
def delete_category(category_id: int) -> None:
    """Delete a category and all its subcategories.

    Raises:
        HTTPException 404: If the category does not exist.
    """
    with get_session() as session:
        category = session.get(Category, category_id)
        if category is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoría con id={category_id} no encontrada",
            )

        subcategories = session.exec(
            select(SubCategory).where(SubCategory.category_id == category_id)
        ).all()
        for sub in subcategories:
            session.delete(sub)

        session.delete(category)
        session.commit()


# ---------------------------------------------------------------------------
# SubCategory CRUD
# ---------------------------------------------------------------------------


@router.post(
    "/categories/{category_id}/subcategories",
    response_model=SubCategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear subcategoría",
)
def create_subcategory(category_id: int, payload: SubCategoryCreate) -> SubCategoryRead:
    """Create a subcategory under an existing category.

    Raises:
        HTTPException 404: If the parent category does not exist.
    """
    with get_session() as session:
        if session.get(Category, category_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoría con id={category_id} no encontrada",
            )
        subcategory = SubCategory(name=payload.name, category_id=category_id)
        session.add(subcategory)
        session.commit()
        session.refresh(subcategory)
        return SubCategoryRead.model_validate(subcategory)


@router.put(
    "/subcategories/{subcategory_id}",
    response_model=SubCategoryRead,
    summary="Editar subcategoría",
)
def update_subcategory(subcategory_id: int, payload: SubCategoryUpdate) -> SubCategoryRead:
    """Update the name of an existing subcategory.

    Raises:
        HTTPException 404: If the subcategory does not exist.
    """
    with get_session() as session:
        subcategory = session.get(SubCategory, subcategory_id)
        if subcategory is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subcategoría con id={subcategory_id} no encontrada",
            )
        if payload.name is not None:
            subcategory.name = payload.name

        session.add(subcategory)
        session.commit()
        session.refresh(subcategory)
        return SubCategoryRead.model_validate(subcategory)


@router.delete(
    "/subcategories/{subcategory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar subcategoría",
)
def delete_subcategory(subcategory_id: int) -> None:
    """Delete a subcategory.

    Raises:
        HTTPException 404: If the subcategory does not exist.
    """
    with get_session() as session:
        subcategory = session.get(SubCategory, subcategory_id)
        if subcategory is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subcategoría con id={subcategory_id} no encontrada",
            )
        session.delete(subcategory)
        session.commit()
