# Solaris Monitoring

API para monitorear celdas y paneles fotovoltaicos, con análisis de eficiencia, detección de anomalías y soporte para dispositivos IoT.

## Características

- API REST con FastAPI.
- Persistencia con SQLAlchemy y migraciones Alembic.
- PostgreSQL en Docker y SQLite para desarrollo y pruebas.
- Arquitectura separada por routers, servicios, repositorios, esquemas y dominio.
- Panel HTML servido por `/` y actualizado con el estado de `/health`.
- CI/CD con Ruff, Mypy, Pytest, cobertura mínima del 90 %, migraciones y build Docker.

## Inicio rápido

### Desarrollo local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn main:app --app-dir src --reload
```

Abre `http://localhost:8000/` para ver el panel, `http://localhost:8000/health` para el estado JSON y `http://localhost:8000/docs` para Swagger.

### Docker Compose

```bash
docker compose up --build -d
curl http://localhost:8000/health
docker compose down
```

La API utiliza `DATABASE_URL`; consulta `.env.example` para las variables disponibles.

## Estructura

```text
src/
├── main.py                 # Aplicación FastAPI y registro de routers
├── db.py                   # Motor, sesión y base SQLAlchemy
└── utils/
    ├── domain/             # Reglas de eficiencia y anomalías
    ├── models/             # Modelos SQLAlchemy
    ├── repositories/       # Persistencia
    ├── routers/            # Endpoints HTTP, incluido /health
    ├── schemas/            # Contratos Pydantic
    ├── services/           # Casos de uso
    └── public/index.html   # Panel de estado
```

## Endpoints

- `GET /`: panel de estado de Solaris Monitoring.
- `GET /health`: estado de la API y fecha de actualización configurada.
- `GET /docs`: documentación OpenAPI.
- `POST /api/v1/cells` y `GET /api/v1/cells`: gestión de celdas.
- `POST /api/v1/readings` y `GET /api/v1/readings`: recepción y consulta de lecturas.
- `GET /api/v1/readings/cell/{cell_id}/summary`: resumen de eficiencia.

`UPDATE_DATE` acepta fechas con formato `YYYY-MM-DD`. Si la configuración es inválida, `/health` informa estado `degraded` y el panel lo refleja automáticamente.

## Calidad y pruebas

Los comandos locales equivalentes al CI son:

```bash
ruff check .
ruff format --check .
mypy src tests
pytest --cov=src --cov-report=term-missing --cov-report=xml
alembic upgrade head
```

La cobertura mínima está definida en `pyproject.toml` y es del 90 %.

## Despliegue

El `Dockerfile` ejecuta las migraciones antes de iniciar Uvicorn. `render.yaml` contiene la configuración base para Render. La documentación adicional está en [docs/API.md](docs/API.md), [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) y [docs/ESP32_INTEGRATION.md](docs/ESP32_INTEGRATION.md).

## Contribución

Usa ramas de trabajo, añade pruebas para los cambios y ejecuta las validaciones del CI antes de abrir un Pull Request. El uso de IA y las decisiones relevantes deben registrarse en [docs/ai_logs/AI_LOG_Lyla.md](docs/ai_logs/AI_LOG_Lyla.md) o en el log correspondiente al integrante.

## Licencia

MIT. Consulta [LICENSE](LICENSE).
