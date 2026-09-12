# ☀️ Solaris Monitoring ☀️

Proyecto desarrollado para el reto **"De la idea a producción en veintiún días"** del curso *DE LA ELECTRÓNICA AL DESARROLLO DE SOFTWARE CON IA*. Este repositorio contiene el desarrollo backend de una API robusta para la gestión y monitoreo de métricas de paneles solares (voltaje, corriente, potencia y energía acumulada).

## Stack Tecnológico

*   **Framework API:** FastAPI (Python 3.12+)
*   **Base de Datos:** PostgreSQL
*   **ORM y Migraciones:** SQLAlchemy y Alembic
*   **Contenedorización:** Docker & Docker Compose
*   **CI/CD & Calidad:** GitHub Actions, Ruff, MyPy, Pytest (Cobertura mínima del 90%)

## Estructura del Proyecto

El repositorio sigue un orden arquitectónico estricto basado en modularidad:

*   `src/`: Código fuente principal de la aplicación.
    *   `main.py`: Punto de entrada de FastAPI.
    *   `models.py`: Modelos de la base de datos (SQLAlchemy).
    *   `sensor_simulado.py`: Script generador de carga útil realista para testear los endpoints de recolección de métricas.
    *   `public/`: Códigos HTML
        *   `index.html`: Base de las páginas
*   `docs/`: Documentación del proyecto.
*   `.github/`: Flujos de automatización CI/CD, configuración de versionado semántico y plantillas de Issues (Bug, Pregunta, Tarea de Desarrollo, etc.).
*   `.tests_check/`: Carpeta para los testeos realizados a mano desde la computadora del usuario
*   `tests/`: Carpeta para los tests de la API previo a su merge con main branch

## Despliegue Local

Para levantar el entorno completo de desarrollo con la base de datos PostgreSQL y la API interconectada, necesitas tener Docker Desktop instalado y ejecutándose.

1. Clona el repositorio e ingresa a la carpeta raíz.
2. Construye y levanta los contenedores usando Docker Compose:
    ```bash
    docker-compose up --build -d
    ```
3. Comprueba que los servicios estén ejecutándose:
    ```bash
    docker-compose ps
    ```
4. Verifica la API en `http://localhost:8000/health` o con:
    ```bash
    curl http://localhost:8000/health
    ```

La API se publica en el puerto `8000`. PostgreSQL se publica en el puerto `5433` del equipo local y mantiene el puerto interno `5432` para la comunicación con la API.

Para detener los servicios:

```bash
docker-compose down
```

Para eliminar también los datos persistidos de PostgreSQL, usa `docker-compose down -v`.

### Ejecución manual de la API

Si solo necesitas ejecutar la API fuera de Docker:

1. Crea y activa un entorno virtual:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```
2. Instala las dependencias de desarrollo:
    ```bash
    pip install -r requirements-dev.txt
    ```
3. Inicia el servidor:
    ```bash
    uvicorn src.main:app --reload
    ```

La documentación interactiva queda disponible en `http://localhost:8000/docs`.

### Estado y fecha de actualización

El endpoint `/health` devuelve `service_status` y `update_date`. El estado se
calcula al responder la petición: `operational` indica que la API está disponible
y `degraded` indica una configuración inválida.

Al crear una tarea con la plantilla `tarea_desarrollo`, registra `update_date`
como `YYYY-MM-DD`. Antes de desplegar la tarea, configura esa misma fecha en la
variable `UPDATE_DATE` del servicio de Render (o en el entorno local). GitHub
Issues sirve como registro de la decisión, mientras que Render inyecta el valor
que consume la API.

La página publicada en GitHub Pages puede consultar una API remota con la URL
del servicio: `index.html?api=https://tu-api.onrender.com`.

### Simulación de lecturas

Con la API ejecutándose, abre otra terminal y lanza el sensor simulado:

```bash
python3 src/sensor_simulado.py
```