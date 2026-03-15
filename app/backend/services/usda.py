"""USDA FoodData Central API service.

Fetches per-100g macro values for a single ingredient by querying the
FoodData Central search endpoint and reading the first result.

Ingredient names are automatically translated to English via GPT-4o mini
before querying USDA, since the database is English-only.
A simple in-memory cache avoids duplicate translation calls within the
same server session.

API key (free): https://fdc.nal.usda.gov/api-guide.html
Docs:           https://app.swaggerhub.com/apis/fdcnal/food-data_central_api/1.0.1
"""

import os
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv
from openai import AsyncOpenAI, AuthenticationError

load_dotenv()

USDA_API_KEY: str = os.getenv("USDA_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
USDA_SEARCH_URL: str = "https://api.nal.usda.gov/fdc/v1/foods/search"

# Nutrient IDs used in the FoodData Central response
_NUTRIENT_KCAL = 1008   # Energy (kcal)
_NUTRIENT_PROT = 1003   # Protein (g)
_NUTRIENT_HC   = 1005   # Carbohydrate, by difference (g)
_NUTRIENT_FAT  = 1004   # Total lipid / fat (g)

# In-memory translation cache: {"huevo": "egg", "patata": "potato", ...}
_translation_cache: dict[str, str] = {}


@dataclass
class NutritionResult:
    """Macro values per 100 g of a single ingredient."""

    kcal_100g: float
    prot_100g: float
    hc_100g: float
    fat_100g: float


_ZERO_RESULT = NutritionResult(kcal_100g=0, prot_100g=0, hc_100g=0, fat_100g=0)


class USDAAuthError(Exception):
    """Raised when USDA rejects the API key (HTTP 403)."""


async def _translate_to_english(name: str) -> str:
    """Translate an ingredient name to English using GPT-4o mini.

    Results are cached in ``_translation_cache`` so each unique name is
    only translated once per server session.

    Args:
        name: Ingredient name in any language.

    Returns:
        English ingredient name, or the original *name* if translation fails
        or OpenAI is not configured.
    """
    cached = _translation_cache.get(name)
    if cached:
        return cached

    if not OPENAI_API_KEY:
        return name

    try:
        client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Translate the food ingredient to English. "
                        "Reply with ONLY the translated ingredient name, "
                        "nothing else. Keep it generic (no brand names)."
                    ),
                },
                {"role": "user", "content": name},
            ],
            temperature=0,
            max_tokens=20,
        )
        translated = response.choices[0].message.content.strip()
    except (AuthenticationError, Exception):
        # If translation fails for any reason, fall back to original name
        return name

    _translation_cache[name] = translated
    return translated


async def get_nutrition(ingredient_name: str) -> NutritionResult:
    """Fetch per-100g macro values for *ingredient_name* via USDA FoodData Central.

    The ingredient name is translated to English before querying USDA.
    All values in the search response are already expressed per 100 g.

    Args:
        ingredient_name: Free-text ingredient name in any language
                         (e.g. "pechuga de pollo").

    Returns:
        A :class:`NutritionResult` with kcal, protein, carbs and fat per 100 g.
        Returns zero-filled result if no match is found or credentials are
        not configured.

    Raises:
        USDAAuthError: If the USDA API key is invalid (HTTP 403).
        RuntimeError:  If the API returns an unexpected error.
    """
    if not USDA_API_KEY:
        return _ZERO_RESULT

    english_name = await _translate_to_english(ingredient_name)

    params = {
        "query": english_name,
        "api_key": USDA_API_KEY,
        "pageSize": 1,
        "dataType": "Foundation,SR Legacy",  # prioritise raw/whole foods
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(USDA_SEARCH_URL, params=params)
    except httpx.RequestError as exc:
        raise RuntimeError(
            f"USDA: error de red al consultar '{ingredient_name}': {exc}"
        ) from exc

    if response.status_code == 403:
        raise USDAAuthError(
            "USDA: clave inválida o no configurada — "
            "comprueba USDA_API_KEY en el archivo .env"
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"USDA: respuesta inesperada {response.status_code} "
            f"para '{ingredient_name}': {response.text[:200]}"
        )

    data = response.json()
    foods = data.get("foods", [])

    if not foods:
        return _ZERO_RESULT

    # Build a quick lookup {nutrientId: value} from the first result
    nutrients: dict[int, float] = {
        n["nutrientId"]: float(n.get("value", 0))
        for n in foods[0].get("foodNutrients", [])
    }

    return NutritionResult(
        kcal_100g=nutrients.get(_NUTRIENT_KCAL, 0),
        prot_100g=nutrients.get(_NUTRIENT_PROT, 0),
        hc_100g=nutrients.get(_NUTRIENT_HC,   0),
        fat_100g=nutrients.get(_NUTRIENT_FAT,  0),
    )
