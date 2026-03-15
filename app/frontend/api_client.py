"""HTTP client for communicating with the PyPlanner backend."""

import os
from typing import Any

import httpx


class APIClient:
    """Async HTTP client wrapping the PyPlanner REST API.

    All methods raise httpx.HTTPStatusError on non-2xx responses.
    """

    def __init__(self) -> None:
        self.base_url: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    async def get(self, path: str) -> Any:
        """Send a GET request and return the parsed JSON response.

        Args:
            path: API path (e.g. "/recipes").

        Returns:
            Parsed JSON response (dict or list).
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}{path}")
            response.raise_for_status()
            return response.json()

    async def post(self, path: str, data: dict[str, Any]) -> Any:
        """Send a POST request with JSON body and return the parsed response.

        Args:
            path: API path (e.g. "/recipes").
            data: Request body as a dictionary.

        Returns:
            Parsed JSON response.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}{path}", json=data)
            response.raise_for_status()
            return response.json()

    async def put(self, path: str, data: dict[str, Any]) -> Any:
        """Send a PUT request with JSON body and return the parsed response.

        Args:
            path: API path (e.g. "/recipes/1").
            data: Request body as a dictionary.

        Returns:
            Parsed JSON response.
        """
        async with httpx.AsyncClient() as client:
            response = await client.put(f"{self.base_url}{path}", json=data)
            response.raise_for_status()
            return response.json()

    async def delete(self, path: str) -> Any:
        """Send a DELETE request and return the parsed response.

        Args:
            path: API path (e.g. "/recipes/1").

        Returns:
            Parsed JSON response.
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{self.base_url}{path}")
            response.raise_for_status()
            return response.json()
