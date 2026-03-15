"""SQLModel models for Recipe and RecipeIngredient."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.backend.models.category import SubCategory


class Recipe(SQLModel, table=True):
    """A recipe with pre-calculated macro totals.

    Macro totals (kcal, prot_g, hc_g, fat_g) are computed by summing
    the contribution of each RecipeIngredient and stored here for fast
    querying without re-calculation at read time.

    Attributes:
        id: Primary key, auto-generated.
        name: Recipe name, indexed for search.
        subcategory_id: Optional FK to SubCategory.
        instructions_text: Free-text cooking instructions.
        image_url: URL of the recipe image (Unsplash or custom).
        servings: Number of servings the recipe yields.
        kcal: Total kilocalories for the whole recipe.
        prot_g: Total protein in grams.
        hc_g: Total carbohydrates in grams.
        fat_g: Total fat in grams.
        created_at: UTC timestamp of creation.
        ingredients: Related RecipeIngredient rows.
        subcategory: Parent SubCategory relationship.
    """

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    subcategory_id: int | None = Field(default=None, foreign_key="subcategory.id")
    instructions_text: str | None = None
    image_url: str | None = None
    servings: int = Field(default=1)

    # Macro totals — computed from ingredients via USDA, stored for fast reads
    kcal: float = Field(default=0)
    prot_g: float = Field(default=0)
    hc_g: float = Field(default=0)
    fat_g: float = Field(default=0)

    created_at: datetime = Field(default_factory=datetime.utcnow)

    ingredients: list["RecipeIngredient"] = Relationship(back_populates="recipe")
    subcategory: Optional["SubCategory"] = Relationship(back_populates="recipes")


class RecipeIngredient(SQLModel, table=True):
    """A single ingredient line within a Recipe.

    Stores the per-100g macro values returned by USDA FoodData Central so
    that macros can be recalculated locally if servings or quantity changes.

    Attributes:
        id: Primary key, auto-generated.
        recipe_id: FK to the parent Recipe.
        name: Ingredient name as entered by the user (e.g. 'Pechuga de pollo').
        quantity_g: Weight in grams for this ingredient in the recipe.
        kcal_100g: Kilocalories per 100 g (from USDA).
        prot_100g: Protein grams per 100 g (from USDA).
        hc_100g: Carbohydrate grams per 100 g (from USDA).
        fat_100g: Fat grams per 100 g (from USDA).
        recipe: Parent Recipe relationship.
    """

    id: int | None = Field(default=None, primary_key=True)
    recipe_id: int = Field(foreign_key="recipe.id")
    name: str
    quantity_g: float

    # Per-100g values saved from USDA for future recalculation
    kcal_100g: float = Field(default=0)
    prot_100g: float = Field(default=0)
    hc_100g: float = Field(default=0)
    fat_100g: float = Field(default=0)

    recipe: Recipe = Relationship(back_populates="ingredients")
