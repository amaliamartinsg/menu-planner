"""OpenAI GPT-4o mini service — Despensa Virtual (recipe suggestion).

Given a list of available ingredients, asks GPT-4o mini to suggest a
complete recipe and returns a validated :class:`RecipeSuggestion` object.

Docs: https://platform.openai.com/docs/api-reference/chat
"""

import json
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI, AuthenticationError
from pydantic import ValidationError

from app.backend.schemas.recipe import RecipeSuggestion

load_dotenv()

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")


class OpenAIAuthError(Exception):
    """Raised when OpenAI rejects the API key (AuthenticationError)."""

SYSTEM_PROMPT = """Eres un chef experto en nutrición.
Cuando el usuario te dé una lista de ingredientes disponibles,
propón UNA receta completa y devuelve SOLO un JSON válido con esta estructura exacta:
{
  "name": "Nombre de la receta",
  "category_suggestion": "Comida",
  "servings": 2,
  "instructions_text": "Instrucciones paso a paso...",
  "ingredients": [
    {"name": "Pechuga de pollo", "quantity_g": 200},
    {"name": "Arroz integral", "quantity_g": 100}
  ]
}
No incluyas texto fuera del JSON."""


async def suggest_recipe(available_ingredients: list[str]) -> RecipeSuggestion:
    """Ask GPT-4o mini to suggest a recipe from *available_ingredients*.

    Retries once with ``temperature=0`` if the first attempt produces
    invalid JSON or a response that does not match :class:`RecipeSuggestion`.

    Args:
        available_ingredients: List of ingredient names the user has on hand.

    Returns:
        A validated :class:`RecipeSuggestion` ready to pre-fill the recipe form.

    Raises:
        RuntimeError: If the OpenAI API key is not set, the API call fails,
                      or the response cannot be parsed after the retry.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError(
            "OpenAI: OPENAI_API_KEY no está configurada en el archivo .env"
        )

    client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    ingredients_text = ", ".join(available_ingredients)
    user_message = f"Ingredientes disponibles: {ingredients_text}"

    for attempt, temperature in enumerate([0.7, 0.0]):
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_tokens=800,
            )
        except AuthenticationError as exc:
            raise OpenAIAuthError(
                "OpenAI: clave inválida o no configurada — "
                "comprueba OPENAI_API_KEY en el archivo .env"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"OpenAI: error al llamar a la API (intento {attempt + 1}): {exc}"
            ) from exc

        raw_content = response.choices[0].message.content or ""

        try:
            data = json.loads(raw_content)
            return RecipeSuggestion.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            if attempt == 0:
                # Will retry with temperature=0
                continue
            raise RuntimeError(
                f"OpenAI: la respuesta no es un JSON válido tras 2 intentos. "
                f"Último error: {exc}. Respuesta recibida: {raw_content[:300]}"
            ) from exc

    # Should never reach here, but keeps the type checker happy
    raise RuntimeError("OpenAI: no se pudo obtener una sugerencia válida")
