# EDSIA Beyond - Photovoltaic Monitor API

API REST profesional para monitoreo y gestión de eficiencia de celdas fotovoltaicas conectadas a IoT (ESP32).

## 🎯 Características

✅ **API REST** completa con FastAPI  
✅ **Base de datos** PostgreSQL con SQLAlchemy ORM  
✅ **Docker & Docker Compose** para desarrollo y producción  
✅ **GitHub Actions** CI/CD automático  
✅ **Documentación interactiva** Swagger UI y ReDoc  
✅ **Tests automatizados** con pytest (>90% coverage)  
✅ **Deploy en Render.com** con un click  
✅ **Integración IoT** con ESP32 (Arduino/MicroPython)  

## 🚀 Quick Start

### Con Docker (Recomendado)

```bash
# Clonar repositorio
git clone <repo-url>
cd EDSIA-Beyond

# Levantar servicios
docker-compose up -d

# Acceder a API
curl http://localhost:8000/health
open http://localhost:8000/docs
```

### Sin Docker

```bash
# Crear virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar API
uvicorn edsia_beyond.main:app --reload
```

## 📚 Documentación

- **[API.md](docs/API.md)** - Referencia completa de endpoints
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Guía de deploy local y producción
- **[ESP32_INTEGRATION.md](docs/ESP32_INTEGRATION.md)** - Código y hardware para IoT

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────┐
│           FastAPI Application                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────┐  ┌──────────────┐                │
│  │   Routers    │  │  Services    │                │
│  │  (Endpoints) │→ │(Business     │                │
│  │              │  │ Logic)       │                │
│  └──────────────┘  └──────────────┘                │
│         ↓                  ↓                        │
│  ┌──────────────────────────────────┐              │
│  │    Repositories (Data Access)    │              │
│  └──────────────────────────────────┘              │
│         ↓                                          │
│  ┌──────────────────────────────────┐              │
│  │    SQLAlchemy ORM + Models       │              │
│  └──────────────────────────────────┘              │
│         ↓                                          │
└─────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────┐
│    PostgreSQL Database                              │
│  ├─ photovoltaic_cells (tabla de celdas)           │
│  └─ readings (tabla de lecturas)                   │
└─────────────────────────────────────────────────────┘
```

## 📦 Stack Tecnológico

| Componente | Herramienta |
|-----------|-----------|
| Framework | FastAPI 0.104+ |
| ORM | SQLAlchemy 2.0 + Alembic |
| Base de Datos | PostgreSQL (prod) / SQLite (dev) |
| Validación | Pydantic 2.0 |
| Testing | pytest + pytest-cov |
| Linting | Ruff + mypy |
| Contenedores | Docker + Docker Compose |
| CI/CD | GitHub Actions |
| Cloud | Render.com |

## 🔌 Endpoints Principales

### Celdas
```
POST   /api/v1/cells              # Crear celda (409 si el nombre existe)
GET    /api/v1/cells              # Listar celdas
GET    /api/v1/cells/active       # Listar sólo celdas activas
GET    /api/v1/cells/{id}         # Obtener celda
PUT    /api/v1/cells/{id}         # Actualizar (recalcula max_safe_voltage)
DELETE /api/v1/cells/{id}         # Eliminar celda y sus lecturas
```

### Lecturas (desde ESP32)
```
POST   /api/v1/readings           # Crear lectura (404 celda desconocida, 409 inactiva)
GET    /api/v1/readings           # Listar lecturas
GET    /api/v1/readings/{id}      # Obtener lectura
GET    /api/v1/readings/cell/{id} # Lecturas de una celda
GET    /api/v1/readings/cell/{id}/summary  # Resumen de eficiencia
```

Contrato completo y reglas de negocio en [docs/API.md](docs/API.md).

## 🧱 Diseño (SOLID)

| Principio | Cómo se aplica |
|---|---|
| **S** — Responsabilidad única | `domain/analysis.py` calcula eficiencia y detecta anomalías; los repositorios sólo persisten; los servicios sólo orquestan |
| **O** — Abierto/cerrado | Una nueva regla de anomalía es una clase más dentro de `CompositeAnomalyDetector`; no se modifica el servicio |
| **L** — Sustitución de Liskov | Todos los detectores respetan el mismo contrato y son intercambiables |
| **I** — Segregación de interfaces | `ReadingService` depende de `CellLookup` (sólo lectura), no del `CellRepository` completo |
| **D** — Inversión de dependencias | Los servicios reciben protocolos por constructor; `dependencies.py` es el único punto que conoce SQLAlchemy |

El dominio (`src/edsia_beyond/domain/`) no importa SQLAlchemy ni FastAPI: son reglas
puras, testeables sin base de datos.

### Salud
```
GET    /health                    # Health check
GET    /docs                      # Swagger UI
GET    /redoc                     # ReDoc
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con reporte de cobertura
pytest --cov=src/edsia_beyond --cov-report=html

# Tests específicos
pytest tests/test_cells.py -v
```

## 🐳 Docker

### Desarrollo
```bash
# Levantar stack completo
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Ejecutar tests dentro del contenedor
docker-compose exec api pytest

# Detener
docker-compose down
```

### Producción (Render.com)

1. Conectar repositorio GitHub a Render
2. Crear `render.yaml` (incluido en repo)
3. Crear PostgreSQL managed en Render
4. Deploy automático en push a `main`

## 📊 Flujo IoT

```
┌─────────────────┐
│   ESP32 Device  │  Lee voltaje → POST /api/v1/readings
│   + ADC Sensor  │
└────────┬────────┘
         ↓
┌─────────────────────────────────┐
│    EDSIA Beyond API             │
│  Calcula eficiencia             │
│  Detecta anomalías              │
└────────┬────────────────────────┘
         ↓
┌─────────────────────────────────┐
│    PostgreSQL Database          │
│  Almacena lecturas              │
└──────────────────────────────────┘
         ↑
┌─────────────────────────────────┐
│    Dashboard / Analytics        │
│  Consume GET /api/v1/readings   │
└──────────────────────────────────┘
```

## 💾 Base de Datos

### Tabla: photovoltaic_cells
```sql
id (PK)
name (UNIQUE)
location
rated_voltage
max_safe_voltage
efficiency_threshold
is_active
```

### Tabla: readings
```sql
id (PK)
cell_id (FK)
voltage_measured
efficiency_percentage (calculado)
is_anomaly (bool)
timestamp
created_at
```

## ⚙️ Configuración

Crear `.env` basado en `.env.example`:

```env
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/edsia_db
ENVIRONMENT=development
DEBUG=False
```

## 🤝 Contribuciones

1. Fork el repositorio
2. Crear rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m "Add nueva-funcionalidad"`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Abrir Pull Request

## ✅ Checklist Pre-Deploy

- [ ] Tests pasando (`pytest`)
- [ ] Linting sin errores (`ruff check src/`)
- [ ] Type checking OK (`mypy src/`)
- [ ] Cobertura >90% (`pytest --cov`)
- [ ] Variables de entorno configuradas
- [ ] Base de datos migrada
- [ ] Health check respondiendo
- [ ] Documentación actualizada

## 📝 Licencia

MIT License - ver LICENSE para detalles

## 📞 Contacto

Para preguntas sobre este proyecto, contactar al equipo EDSIA.

---

**Última actualización:** Septiembre 2026  
**Versión:** 1.0.0
