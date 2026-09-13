# Device Authentication with API Key - Solaris Monitoring

## Implementación de Autenticación de Dispositivos con API Key

### Problema Resuelto
Como administrador del sistema, necesitaba que solo los dispositivos autorizados puedan registrar lecturas en la API, para evitar que cualquiera que vea `/docs` en producción pueda falsear la eficiencia de las celdas solares insertando datos maliciosos.

### Cambios Implementados

#### 1. Configuración (`src/utils/config.py`)
- ✅ Agregado campo `device_api_key: str | None = None` en `Settings`
- ✅ Validación de startup: si `environment=production` y `DEVICE_API_KEY` no está definida, la app falla con `ValueError`
- ✅ Variable de entorno: `DEVICE_API_KEY` (nunca hardcodeada)

#### 2. Infraestructura de Dependencias (`src/main.py`, `src/utils/dependencies.py`)
- ✅ Global `_current_settings: Settings | None = None` para inyección de dependencias
- ✅ Función `get_settings()` accesible desde toda la app
- ✅ `APIKeyHeader(name="X-API-Key")` para integración automática con Swagger
- ✅ `verify_api_key()` con `secrets.compare_digest()` (defensa contra timing attacks)
- ✅ Tipo `ApiKeyDep = Annotated[str, Depends(verify_api_key)]` para reutilización

#### 3. Protección de Endpoints

**Protegidos (requieren X-API-Key):**
- ✅ `POST /api/v1/readings` - Crear lectura
- ✅ `POST /api/v1/cells` - Crear celda
- ✅ `PUT /api/v1/cells/{cell_id}` - Actualizar celda
- ✅ `DELETE /api/v1/cells/{cell_id}` - Eliminar celda

**Públicos (sin autenticación):**
- ✅ `GET /api/v1/readings` - Listar lecturas
- ✅ `GET /api/v1/cells` - Listar celdas
- ✅ `GET /health` - Estado de la API
- ✅ `/docs` - Documentación Swagger

#### 4. Tests - TDD (126 tests, 100% passing)
- ✅ `test_post_reading_without_api_key_returns_401` - Sin header
- ✅ `test_post_reading_with_wrong_api_key_returns_401` - API key incorrecta
- ✅ `test_post_reading_with_correct_api_key_succeeds` - API key correcta
- ✅ 6 tests análogos para endpoints de celdas (POST, PUT, DELETE)
- ✅ Todos los tests existentes continúan pasando
- ✅ Cobertura: 98.68% (exceeds 90% requirement)

#### 5. Configuración de Entorno

**.env.example:**
```
DEVICE_API_KEY=desarrollo_api_key_ejemplo_sin_usar
```

**render.yaml:**
```yaml
- key: DEVICE_API_KEY
  scope: project
  sync: false  # Variable secreta, configurada manualmente en Render
```

#### 6. Documentación
- ✅ AI_LOG_Lyla.md actualizado con Prompts #32, #33, #34, #35
- ✅ docs/DEPLOYMENT.md incluye guía de configuración
- ✅ README.md actualizado con información de autenticación

### Criterios de Aceptación - Todos Cumplidos ✅

| Criterio | Estado | Evidencia |
|----------|--------|-----------|
| POST /api/v1/readings sin X-API-Key → 401 | ✅ | test_post_reading_without_api_key_returns_401 |
| POST /api/v1/readings con clave incorrecta → 401 | ✅ | test_post_reading_with_wrong_api_key_returns_401 |
| POST /api/v1/readings con clave correcta → 201 | ✅ | test_post_reading_with_correct_api_key_succeeds |
| POST/PUT/DELETE /api/v1/cells protegidos | ✅ | 6 tests de autenticación PASSED |
| GET endpoints públicos (sin auth) | ✅ | Todos los tests GET pasan sin headers |
| /health público | ✅ | test_health_returns_200 PASSED |
| /docs público | ✅ | Swagger accesible sin autenticación |
| Swagger "Authorize" button visible | ✅ | APIKeyHeader integrado automáticamente |
| App falla si falta DEVICE_API_KEY en producción | ✅ | ValueError en Settings.from_env() |
| Cobertura ≥ 90% | ✅ | 98.68% (489 statements) |
| Ruff limpio | ✅ | All checks passed! |
| Mypy limpio | ✅ | No issues found in 45 source files |

### Archivos Modificados

```
.env.example                              # Agregar DEVICE_API_KEY
.gitignore                                # Actualizar para .env
README.md                                 # Documentación de API key
docker-compose.yml                        # Usar variables de entorno
docs/DEPLOYMENT.md                        # Guía de configuración
docs/ai_logs/AI_LOG_Lyla.md              # Historial de prompts
render.yaml                               # Variable secreta DEVICE_API_KEY
src/main.py                               # Global settings management
src/utils/config.py                       # Campo DEVICE_API_KEY + validación
src/utils/dependencies.py                 # verify_api_key + ApiKeyHeader
src/utils/routers/cells.py                # Proteger POST/PUT/DELETE
src/utils/routers/readings.py             # Proteger POST
tests/conftest.py                         # TEST_API_KEY fixture
tests/integration/test_cells_api.py       # 6 tests de autenticación
tests/integration/test_readings_api.py    # 3 tests de autenticación + fixes
tests/unit/test_config.py                 # Test DEVICE_API_KEY
```

### Validación Ejecutada

```bash
# Tests: 126 passed, 0 failed, cobertura 98.68%
pytest --cov=src --cov-report=term-missing tests/

# Code quality: sin errores
ruff check .
ruff format .
mypy src tests
```

### Próximos Pasos (Issue #2)

El firmware del ESP32 debe enviar el header `X-API-Key` en todas las solicitudes POST:
```python
headers = {"X-API-Key": DEVICE_API_KEY}
response = requests.post(
    "https://api.solaris-monitoring.com/api/v1/readings",
    json=reading_data,
    headers=headers
)
```

### Notas de Seguridad

- ✅ API key nunca está hardcodeada en código
- ✅ Comparación usa `secrets.compare_digest()` (defensa timing-attack)
- ✅ En producción: variable secreta manual (no sincronizada con repo)
- ✅ En desarrollo: `.env` contiene clave de ejemplo (no versioned)
- ✅ Logs no exponen la API key

---

**Branch:** `lyla`  
**Base:** `main`  
**Tipo:** Feature - Device Authentication  
**Relacionado:** Issue #1 (Seguridad)
