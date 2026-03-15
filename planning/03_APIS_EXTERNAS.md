# 🔑 03 — APIs Externas: Registro y Configuración

> Completa estos pasos **antes de empezar la Fase 2**.
> Las claves van en el archivo `.env` en la raíz del proyecto.

---

## Checklist de Configuración

- [X] Crear archivo `.env` en la raíz del proyecto
- [X] Registrarse en USDA FoodData Central y obtener clave
- [X] Registrarse en Unsplash y obtener clave
- [X] Crear cuenta OpenAI y añadir saldo
- [X] Verificar que las 3 APIs responden correctamente

---

## `.env.example` (copiar como `.env` y rellenar)

```env
# USDA FoodData Central (macros de ingredientes)
USDA_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Unsplash
UNSPLASH_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# App config
BACKEND_URL=http://localhost:8000
DATABASE_URL=sqlite:///./recipe_manager.db
```

---

## 1. USDA FoodData Central — Nutrition API

**Tier gratuito:** ✅ Completamente gratuito, sin límite diario práctico
**Uso en el proyecto:** Obtener macros por 100g de cada ingrediente al guardar una receta

> ⚠️ **Nota:** Edamam fue descartado por requerir tarjeta incluso en el plan básico.
> Se migró a USDA FoodData Central, que es completamente gratuito.

### Pasos de registro

- [X] Ir a [fdc.nal.usda.gov/api-guide.html](https://fdc.nal.usda.gov/api-guide.html)
- [X] Crear cuenta gratuita y solicitar API key
- [X] Copiar la clave → `USDA_API_KEY`

### Flujo real implementado

La base de datos de USDA es en inglés, por lo que los nombres de ingredientes
se traducen automáticamente con GPT-4o mini antes de consultar la API:

```
"pechuga de pollo"
       ↓
  GPT-4o mini (temperature=0, max_tokens=20)
       ↓
  "chicken breast"
       ↓
  USDA FoodData Central
       ↓
  NutritionResult(kcal_100g=165, prot_100g=31, hc_100g=0, fat_100g=3.6)
```

Las traducciones se cachean en memoria (`_translation_cache`) para no
repetir llamadas con el mismo ingrediente durante la sesión del servidor.

### Ejemplo de llamada

```python
# GET https://api.nal.usda.gov/fdc/v1/foods/search
# Params: query="chicken breast", api_key=KEY, pageSize=1, dataType="Foundation,SR Legacy"

params = {
    "query": "chicken breast",   # nombre ya traducido al inglés
    "api_key": USDA_API_KEY,
    "pageSize": 1,
    "dataType": "Foundation,SR Legacy",  # prioriza alimentos crudos/enteros
}
```

### Respuesta relevante

```json
{
  "foods": [
    {
      "description": "Chicken, broilers or fryers, breast, meat only, raw",
      "foodNutrients": [
        { "nutrientId": 1008, "nutrientName": "Energy",                    "value": 120 },
        { "nutrientId": 1003, "nutrientName": "Protein",                   "value": 22.5 },
        { "nutrientId": 1005, "nutrientName": "Carbohydrate, by difference","value": 0 },
        { "nutrientId": 1004, "nutrientName": "Total lipid (fat)",          "value": 2.62 }
      ]
    }
  ]
}
```

Los valores ya están expresados por 100g — no es necesario normalizar.

### IDs de nutrientes usados

| ID   | Nutriente               | Campo interno |
|------|-------------------------|---------------|
| 1008 | Energy                  | `kcal_100g`   |
| 1003 | Protein                 | `prot_100g`   |
| 1005 | Carbohydrate (by diff.) | `hc_100g`     |
| 1004 | Total lipid (fat)       | `fat_100g`    |

### Manejo de errores

| Situación                  | Comportamiento                              |
|----------------------------|---------------------------------------------|
| Ingrediente no encontrado  | Devuelve `NutritionResult` con todos 0      |
| `USDA_API_KEY` vacía       | Devuelve `NutritionResult` con todos 0      |
| HTTP 403 (clave inválida)  | Lanza `USDAAuthError` → endpoint devuelve **403** |
| Otro error HTTP / red      | Lanza `RuntimeError` → endpoint devuelve **502** |

---

## 2. Unsplash — Image Search API

**Tier gratuito:** 50 requests/hora ✅ (modo Demo)
**Uso en el proyecto:** Mostrar carrusel de 3-5 imágenes al crear/sugerir receta

### Pasos de registro

- [X] Ir a [unsplash.com/developers](https://unsplash.com/developers)
- [X] Click en **"Your apps"** → **"New Application"**
- [X] Aceptar términos (uso no comercial / demo está bien para uso personal)
- [X] Nombre: `recipe-manager-mvp`
- [X] Copiar **"Access Key"** → `UNSPLASH_ACCESS_KEY`

### Ejemplo de llamada

```python
# GET https://api.unsplash.com/search/photos

params = {
    "query": query,
    "per_page": count,           # máx 30
    "orientation": "landscape",
    "client_id": UNSPLASH_ACCESS_KEY,
}
# Devuelve: [photo["urls"]["regular"] for photo in data["results"]]
```

### Manejo de errores

| Situación                  | Comportamiento                                        |
|----------------------------|-------------------------------------------------------|
| `UNSPLASH_ACCESS_KEY` vacía | Devuelve lista vacía `[]`                            |
| HTTP 401 (token inválido)  | Lanza `UnsplashAuthError` → endpoint devuelve **403** |
| Otro error HTTP / red      | Lanza `RuntimeError` → endpoint devuelve **502**      |

### Notas importantes
- Usar `urls.regular` (no `full`) — buen balance calidad/tamaño
- Solo guardamos la URL elegida por el usuario (no descargamos la imagen)

---

## 3. OpenAI — GPT-4o mini

**Tier gratuito:** ❌ Requiere saldo (prepago)
**Coste estimado:** ~$0.01-0.05 por sugerencia de receta + ~$0.0001 por traducción de ingrediente
**Uso en el proyecto:**
  1. **Despensa Virtual** — sugerir receta a partir de ingredientes disponibles
  2. **Traducción de ingredientes** — convertir nombres en español a inglés antes de consultar USDA

### Pasos de configuración

- [X] Ir a [platform.openai.com](https://platform.openai.com)
- [X] Ir a **"Billing"** → añadir método de pago → cargar $5-10 (dura meses)
- [X] Ir a **"API Keys"** → **"Create new secret key"**
- [X] Copiar clave → `OPENAI_API_KEY`

### Uso 1 — Traducción de ingredientes (en `services/usda.py`)

```python
# Llamada mínima: temperature=0, max_tokens=20
response = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Translate the food ingredient to English. "
                                      "Reply with ONLY the translated ingredient name."},
        {"role": "user", "content": "pechuga de pollo"},
    ],
    temperature=0,
    max_tokens=20,
)
# → "chicken breast"
```

### Uso 2 — Sugerencia de receta (en `services/openai_service.py`)

```python
SYSTEM_PROMPT = """Eres un chef experto en nutrición.
Propón UNA receta y devuelve SOLO un JSON válido con esta estructura:
{
  "name": "Nombre de la receta",
  "category_suggestion": "Comida",
  "servings": 2,
  "instructions_text": "Instrucciones paso a paso...",
  "ingredients": [
    {"name": "Pechuga de pollo", "quantity_g": 200}
  ]
}
No incluyas texto fuera del JSON."""
```

### Manejo de errores

| Situación                         | Comportamiento                                         |
|-----------------------------------|--------------------------------------------------------|
| `OPENAI_API_KEY` vacía            | Traducción: devuelve nombre original sin error         |
| Clave inválida (`AuthenticationError`) | Lanza `OpenAIAuthError` → endpoint devuelve **403** |
| JSON inválido en suggest_recipe   | Reintenta con `temperature=0`; si falla → **502**      |
| Cualquier otro error en traducción | Devuelve nombre original (fallback silencioso)        |

---

## Script de Verificación de APIs

Ejecutar desde la raíz con las claves ya configuradas en `.env`:

```python
"""Script para verificar que las 3 APIs responden correctamente."""
import asyncio
import httpx
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

async def test_usda():
    print("🥗 Testando USDA FoodData Central...")
    url = "https://api.nal.usda.gov/fdc/v1/foods/search"
    params = {
        "query": "chicken breast",
        "api_key": os.getenv("USDA_API_KEY"),
        "pageSize": 1,
        "dataType": "Foundation,SR Legacy",
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params)
        if r.status_code == 200:
            foods = r.json().get("foods", [])
            if foods:
                nutrients = {n["nutrientId"]: n["value"] for n in foods[0]["foodNutrients"]}
                print(f"  ✅ USDA OK — chicken breast: {nutrients.get(1008, 0):.0f} kcal/100g")
            else:
                print("  ⚠️  USDA OK pero sin resultados para 'chicken breast'")
        else:
            print(f"  ❌ USDA ERROR: {r.status_code} — {r.text[:200]}")

async def test_unsplash():
    print("🖼️  Testando Unsplash...")
    url = "https://api.unsplash.com/search/photos"
    params = {"query": "pasta carbonara", "per_page": 1, "client_id": os.getenv("UNSPLASH_ACCESS_KEY")}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            print(f"  ✅ Unsplash OK — {data['total']} resultados para 'pasta carbonara'")
        else:
            print(f"  ❌ Unsplash ERROR: {r.status_code}")

async def test_openai():
    print("🤖 Testando OpenAI...")
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    try:
        r = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Di solo: OK"}],
            max_tokens=10,
        )
        print(f"  ✅ OpenAI OK — respuesta: {r.choices[0].message.content}")
    except Exception as e:
        print(f"  ❌ OpenAI ERROR: {e}")

async def main():
    await test_usda()
    await test_unsplash()
    await test_openai()
    print("\n✅ Test completado")

asyncio.run(main())
```
