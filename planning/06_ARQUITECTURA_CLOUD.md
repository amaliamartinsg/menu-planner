## ☁️ Arquitectura Cloud (GCP - Python Optimized)

Para maximizar el rendimiento y minimizar costes (aprovechando los $300 de prueba), la infraestructura se basa en servicios *Serverless*:

### 1. Cómputo (Backend & Frontend)
* *Servicio:* [Google Cloud Run](https://cloud.google.com/run).
* *Configuración:* Contenedores Docker para *FastAPI* (Backend) y *Flet* (Frontend Web/PWA).
* *Estrategia:* Configurar min-instances: 0. Solo pagas cuando alguien usa la app. Es ideal para Python ya que Cloud Run gestiona la concurrencia eficientemente.

### 2. Base de Datos (Persistencia)
* *Opción A (Relacional):* [Cloud SQL for PostgreSQL](https://cloud.google.com/sql). Instancia db-f1-micro. Es la más económica para usar con SQLAlchemy/SQLModel.
* *Opción B (NoSQL - Recomendada para Free Tier):* [Firestore](https://cloud.google.com/firestore). Tiene una capa gratuita generosa (50k lecturas/día) y se integra nativamente con Python.

### 3. Almacenamiento de Imágenes
* *Servicio:* [Cloud Storage](https://cloud.google.com/storage).
* *Uso:* Guardar las fotos de las recetas que elijas. Los primeros 5GB son gratuitos.

### 4. Gestión de Secretos e IA
* *Secret Manager:* Para guardar las API Keys de USDA (macros), Unsplash (imágenes) y OpenAI (sugerencias + traducción) de forma segura.
* *Cloud Build:* Para el despliegue automático (CI/CD) desde tu repositorio de GitHub.

### 5. Red y Acceso
* *Firebase Hosting:* Como "espejo" para servir el frontend de Flet con SSL gratuito y latencia mínima en móviles.
