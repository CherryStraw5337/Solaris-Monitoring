# Customización de Agentes de IA para Solaris Monitoring

Este archivo ayuda a los agentes de IA de programación a ser inmediatamente productivos en el codebase de Solaris Monitoring.

## Comandos de Inicio Rápido

### Desarrollo Local
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn main:app --app-dir src --reload
```

### Configuración Docker
```bash
docker compose up --build -d
curl http://localhost:8000/health
docker compose down
```

### Calidad de Código (Requerido antes de PRs)
```bash
ruff check .              # Validación de lint
ruff format --check .    # Validación de formato
mypy src tests           # Verificación de tipos
pytest --cov=src --cov-report=term-missing --cov-report=xml  # Tests + cobertura (mín 90%)
```

### Migraciones de Base de Datos
```bash
alembic upgrade head     # Aplicar migraciones
alembic revision --autogenerate -m "Descripción"  # Crear nueva migración
```

## Arquitectura y Patrones de Diseño

### Arquitectura de 4 Capas (carpeta src/)

```
Routers (endpoints API) → Schemas (modelos Pydantic)
                ↓
        Services (lógica de negocio)
                ↓
    Repositories (acceso a datos)
                ↓
Models (SQLAlchemy ORM)
```

**Archivos Clave por Responsabilidad:**
- **Routers** (`src/utils/routers/`): Endpoints HTTP, validación de solicitudes
  - `cells.py`: Operaciones CRUD para celdas fotovoltaicas
  - `readings.py`: Gestión de lecturas de voltaje
  - `health.py`: Endpoint de verificación de salud de la API
- **Schemas** (`src/utils/schemas/`): Modelos Pydantic para validación de entrada/salida
- **Services** (`src/utils/services/`): Lógica de negocio, orquestación
  - `CellService`: Gestiona celdas fotovoltaicas
  - `ReadingService`: Maneja lecturas con análisis (eficiencia, anomalías)
- **Repositories** (`src/utils/repositories/`): Operaciones SQLAlchemy en base de datos
  - Abstracciones basadas en protocolos (`protocols.py`)
  - Implementaciones: `SqlAlchemyCellRepository`, `SqlAlchemyReadingRepository`
- **Domain** (`src/utils/domain/`): Lógica de negocio central independiente del framework
  - `analysis.py`: Cálculos de eficiencia y detección de anomalías
  - `errors.py`: Excepciones del dominio

### Inyección de Dependencias
- Usar patrón `Depends()` de FastAPI (ver [src/utils/dependencies.py](src/utils/dependencies.py))
- Los servicios se instancian nuevos por cada solicitud
- La sesión de BD se gestiona automáticamente mediante el gestor de contexto `get_db()`

### Configuración
- Centralizada en [src/utils/config.py](src/utils/config.py) mediante la clase `Settings`
- Basada en entorno: carga desde `os.environ`
- En producción: `ENVIRONMENT=production` + `DEVICE_API_KEY` son obligatorios
- Auto-normalización de URL de BD para URLs de Render/Heroku

### Seguridad de la API
- **Endpoints de lectura** (`GET`): Públicos, sin autenticación
- **Endpoints de escritura** (`POST/PUT/DELETE`): Requieren encabezado `X-API-Key`
- Usa `secrets.compare_digest()` para prevenir ataques de timing

### Integración MQTT
- Opcional, habilitada solo si la variable de entorno `MQTT_HOST` está configurada
- Hilo de fondo (no bloqueante) iniciado en el lifespan de FastAPI
- Manejado en [src/utils/mqtt_adapter.py](src/utils/mqtt_adapter.py)

## Convenciones y Patrones

### Estilo de Código
- **Longitud de línea**: 100 caracteres (configurado en `pyproject.toml`)
- **Python**: 3.12+
- **Orden de importes**: E (errores) → F (pyflakes) → I (isort) → UP (upgrades) → B (bugbear)
  - Ruff aplica este estilo mediante pre-commit
- **Anotaciones de tipo**: Obligatorias para todas las funciones y métodos (`disallow_untyped_defs = true`)

### Patrones de Base de Datos
- **ORM**: SQLAlchemy 2.0 (API moderna lista para async)
- **Migraciones**: Generadas automáticamente por Alembic a partir de cambios en modelos
- **Timestamps**: Siempre UTC mediante el tipo personalizado `UTCDateTime` en [src/db.py](src/db.py)
  - Todos los objetos `datetime` se normalizan a UTC al escribir y se refuerzan al leer
- **Claves foráneas**: Eliminación en cascada habilitada (ej: eliminar una celda elimina sus lecturas)

### Pruebas
- **Framework**: pytest con pytest-cov
- **Cobertura mínima**: 90% (aplicada en CI)
- **Fixtures**: Compartidas en [tests/conftest.py](tests/conftest.py)
- **Fakes**: Objetos mock en [tests/fakes.py](tests/fakes.py)
- **Estructura de pruebas**:
  - `tests/unit/`: Pruebas de servicios y utilidades
  - `tests/integration/`: Pruebas de endpoints de API mediante `httpx.AsyncClient`
  - `tests/test_smoke.py`: Validación de verificación de salud

### Reglas de Lógica de Negocio
Consultar [docs/API.md](docs/API.md) para reglas:
- **Fórmula de eficiencia**: `(voltage_measured / rated_voltage) * 100`
- **Voltaje máximo seguro**: `rated_voltage * 1.2` (derivado por servidor)
- **Indicadores de anomalía**: Voltaje excede voltaje_máximo_seguro O eficiencia < umbral
- **Tolerancia de reloj del dispositivo**: ±5 minutos (rechazar lecturas del futuro)
- **Celdas inactivas**: No pueden aceptar lecturas nuevas

## Errores Comunes y Soluciones

### 1. **Errores de Tipo con `Callable`**
- **Problema**: mypy reclama sobre `callable` (minúsculas)
- **Solución**: Usar `from typing import Callable` y escribir `Callable[[...], ReturnType]`

### 2. **Importes Sin Usar Después de Limpieza**
- **Problema**: Eliminar código muerto deja importes sin usar
- **Solución**: Ejecutar `ruff check .` antes de hacer commit; Ruff los reportará

### 3. **F-strings Sin Placeholders**
- **Problema**: `f"mensaje"` dispara F541 (f-string-is-literal)
- **Solución**: Usar string plano `"mensaje"` si no hay interpolación

### 4. **Conflictos de Revisión Alembic**
- **Problema**: Múltiples desarrolladores crean migraciones con la misma marca de tiempo
- **Solución**: Rebase y dejar que Alembic renumere o fusionar manualmente archivos `versions/`

### 5. **datetime Sin Zona Horaria**
- **Problema**: SQLite descarta `tzinfo`, resultando en datetimes ingenuos
- **Solución**: Siempre usar `datetime.datetime.now(datetime.timezone.utc)` o confiar en tipo personalizado `UTCDateTime`

### 6. **API Key No Configurada en Producción**
- **Problema**: DEVICE_API_KEY faltante en producción genera `ValueError` al iniciar
- **Solución**: Agregar `DEVICE_API_KEY` como secreto en entorno Render/Docker

### 7. **Conexión MQTT Se Cuelga**
- **Problema**: Hilo MQTT bloquea inicio si broker es inaccesible
- **Solución**: MQTT corre en hilo daemon; no bloqueante. Deshabilitarlo omitiendo `MQTT_HOST`

## Referencias de Documentación

- [docs/API.md](docs/API.md): Endpoints API REST y reglas de negocio
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md): Docker, Render producción, configuración GitHub Actions
- [docs/ESP32_INTEGRATION.md](docs/ESP32_INTEGRATION.md): Integración con dispositivos IoT ESP32
- [docs/adr/](docs/adr/): Architecture Decision Records
- [README.md](README.md): Descripción del proyecto e inicio rápido
- [docs/ai_logs/](docs/ai_logs/): Prompts de IA del equipo y decisiones (ver formato abajo)

## Formato de Registro de IA

Al trabajar con IA, registra tus prompts y decisiones en [docs/ai_logs/](docs/ai_logs/) usando esta estructura:

```markdown
# [Nombre del Integrante] - Prompt #[Número]

### IA Utilizada: GitHub Copilot (Claude Haiku 4.5)

**Prompt del integrante completo:**
> [Prompt completo original aquí]

**Respuesta de la IA completa:**

[Respuesta completa de IA con decisiones clave y cambios]

**Qué se aceptó:** [Qué se mantuvo de la respuesta]
**Qué se denegó:** [Qué se rechazó y por qué]
**Qué se modificó:** [Qué se cambió después de la respuesta]
```

Ejemplo: [docs/ai_logs/AI_LOG_Lyla.md](docs/ai_logs/AI_LOG_Lyla.md)

---

## Al Trabajar en Cambios

1. **Nueva Característica**: Crear rama → Implementar con pruebas → Ejecutar validación CI → PR
2. **Arreglo de Calidad de Código**: Ejecutar `ruff format .`, luego `ruff check .` y `mypy src tests`
3. **Cambio de Base de Datos**: Crear migración Alembic → Probar localmente → Commit con migración
4. **Cambio de API**: Actualizar endpoint → Actualizar esquema Pydantic → Actualizar [docs/API.md](docs/API.md) → Agregar pruebas
5. **Configuración**: Agregar a [src/utils/config.py](src/utils/config.py) → Valor por defecto sensato → Documentar en README

## Pipeline CI/CD

GitHub Actions (`.github/workflows/ci-cd.yml`) se ejecuta en cada push:
1. Lint: `ruff check .`
2. Formato: `ruff format --check .`
3. Verificación de tipos: `mypy src tests`
4. Pruebas: `pytest --cov=src` (cobertura mín 90%)
5. Migraciones: `alembic upgrade head`
6. Build Docker: Imagen multi-stage para producción

Todas las verificaciones deben pasar antes de fusionar. Sin excepciones.
