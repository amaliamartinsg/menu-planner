"""Unsplash Image Search API service.

Returns a list of landscape photo URLs for a given query term.

Docs: https://unsplash.com/documentation#search-photos
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

UNSPLASH_ACCESS_KEY: str = os.getenv("UNSPLASH_ACCESS_KEY", "")
UNSPLASH_URL: str = "https://api.unsplash.com/search/photos"


class UnsplashAuthError(Exception):
    """Raised when Unsplash rejects the access key (HTTP 401)."""


async def search_images(query: str, count: int = 5) -> list[str]:
    """Search Unsplash for food/recipe photos matching *query*.

    Args:
        query: Search term — English terms yield better results
               (e.g. "chicken pasta" instead of "pasta de pollo").
        count: Number of image URLs to return (default 5, max 30).

    Returns:
        List of ``urls.regular`` strings (~1080 px wide).
        Returns an empty list if the access key is not configured.

    Raises:
        RuntimeError: If Unsplash returns an unexpected HTTP error.
    """
    if not UNSPLASH_ACCESS_KEY:
        return []

    params = {
        "query": query,
        "per_page": min(count, 30),
        "orientation": "landscape",
        "client_id": UNSPLASH_ACCESS_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(UNSPLASH_URL, params=params)
    except httpx.RequestError as exc:
        raise RuntimeError(
            f"Unsplash: error de red para query '{query}': {exc}"
        ) from exc

    if response.status_code == 401:
        raise UnsplashAuthError(
            "Unsplash: token inválido o no configurado — "
            "comprueba UNSPLASH_ACCESS_KEY en el archivo .env"
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"Unsplash: respuesta inesperada {response.status_code} "
            f"para query '{query}': {response.text[:200]}"
        )

    data = response.json()
    return [photo["urls"]["regular"] for photo in data.get("results", [])]
