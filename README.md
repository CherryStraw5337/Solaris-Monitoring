# Solaris Monitoring

API para monitorear celdas y paneles fotovoltaicos, con análisis de eficiencia, detección de anomalías y soporte para dispositivos IoT.
[![CI/CD](https://github.com/CherryStraw5337/Solaris-Monitoring/actions/workflows/ci-cd.yml/badge.svg?branch=main)](https://github.com/CherryStraw5337/Solaris-Monitoring/actions/workflows/ci-cd.yml)

**Para quién es:** quien mantiene una instalación fotovoltaica y hoy solo detecta una celda degradada subiendo a medirla con un multímetro.

- **En producción:** [solaris-monitoring-api.onrender.com](https://solaris-monitoring-api.onrender.com/)
- **One-pager ejecutivo:** [docs/ONE_PAGER.md](docs/ONE_PAGER.md)
- **Decisiones de arquitectura:** [docs/adr/](docs/adr/)
- **Proceso, retrospectiva y backlog vivo:** [docs/PROCESO.md](docs/PROCESO.md)

## Características

- API REST con FastAPI con autenticación por API key (X-API-Key).
- Persistencia con SQLAlchemy y migraciones Alembic.
- PostgreSQL en Docker y SQLite para desarrollo y pruebas.
- Arquitectura separada por routers, servicios, repositorios, esquemas y dominio.
- Dashboard web en `/` con eficiencia, anomalías y resumen por celda, alimentado solo por endpoints `GET` públicos.
- Ingesta opcional por MQTT (HiveMQ Cloud, TLS) con las mismas reglas que HTTP; estado visible en `/health` como `mqtt_status` ([ADR-0002](docs/adr/ADR-0002-mqtt-broker.md)).
- CI/CD con Ruff, Mypy, Pytest, cobertura mínima del 90 %, migraciones y build Docker.
- Endpoints protegidos para escritura (POST/PUT/DELETE) con validación de API key.
- Endpoints públicos para lectura (GET) sin autenticación.

## Inicio rápido

### Desarrollo local

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head   # crea o actualiza el esquema; la app no crea tablas al arrancar
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
├── main.py                 # Aplicación FastAPI, gestión global de settings y registro de routers
├── db.py                   # Motor, sesión y base SQLAlchemy
├── public/                 # Dashboard web servido en / (index.html, main.js, style.css)
└── utils/
    ├── config.py           # Configuración centralizada y validación de DEVICE_API_KEY
    ├── dependencies.py     # Inyección de dependencias (verify_api_key, etc.)
    ├── clock.py            # Utilidades de fecha y hora
    ├── exception_handlers.py # Manejadores de excepciones personalizados
    ├── mqtt_listener.py    # Adaptador de entrada MQTT (usa ReadingService)
    ├── domain/             # Reglas de eficiencia y anomalías
    ├── models/             # Modelos SQLAlchemy
    ├── repositories/       # Capa de persistencia
    ├── routers/            # Endpoints HTTP (/health, /api/v1/cells, /api/v1/readings)
    ├── schemas/            # Esquemas Pydantic (contratos de entrada/salida)
    └── services/           # Lógica de negocio y casos de uso

tests/
├── conftest.py             # Fixtures compartidas de pytest
├── fakes.py                # Objetos mock para pruebas
├── test_smoke.py           # Pruebas de humo
├── integration/            # Tests de integración de endpoints
└── unit/                   # Tests unitarios de servicios y utilidades

docs/
├── API.md                  # Documentación de la API REST
├── DEPLOYMENT.md           # Guía de despliegue en Render y Docker
├── ESP32_INTEGRATION.md    # Integración con dispositivos IoT ESP32
├── adr/                    # Architecture Decision Records
└── ai_logs/                # Historiales de prompts y decisiones de IA
```

## Endpoints

### Públicos (sin autenticación)
- `GET /`: panel de estado de Solaris Monitoring.
- `GET /health`: estado de la API y fecha de actualización configurada.
- `GET /docs`: documentación OpenAPI con botón "Authorize" para pruebas.
- `GET /api/v1/cells`: listado de celdas fotovoltaicas.
- `GET /api/v1/readings`: listado de lecturas.
- `GET /api/v1/readings/cell/{cell_id}/summary`: resumen de eficiencia de una celda.

### Protegidos (requieren encabezado `X-API-Key`)
- `POST /api/v1/cells`: registrar nueva celda (requiere API key).
- `PUT /api/v1/cells/{cell_id}`: actualizar celda (requiere API key).
- `DELETE /api/v1/cells/{cell_id}`: eliminar celda (requiere API key).
- `POST /api/v1/readings`: registrar lectura de celda (requiere API key).

### Autenticación
La API usa esquema de autenticación por encabezado `X-API-Key` (APIKeyHeader de FastAPI). Para utilizar endpoints protegidos:

```bash
curl -H "X-API-Key: your-api-key" -X POST http://localhost:8000/api/v1/cells -d '...'
```

La variable de entorno `DEVICE_API_KEY` debe configurarse. En producción, es obligatoria.

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

Deploy en Render: [https://solaris-monitoring-api.onrender.com/](https://solaris-monitoring-api.onrender.com/)

## Contribución

Usa ramas de trabajo, añade pruebas para los cambios y ejecuta las validaciones del CI antes de abrir un Pull Request.

### Historial de Decisiones y Prompts de IA

El proyecto documenta el uso de IA en la carpeta [docs/ai_logs/](docs/ai_logs/). Cada miembro del equipo mantiene un log con formato estándar:

- **Nombre de integrante - Prompt #(número)**
- **IA utilizada** (ej: GitHub Copilot Claude Haiku 4.5)
- **Prompt completo del integrante**
- **Respuesta de la IA**
- **Qué se aceptó / modificó / denegó**

## Licencia

MIT. Consulta [LICENSE](LICENSE).
