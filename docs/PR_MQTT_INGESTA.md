# PR: MQTT Ingesta - IoT Input Channel for Solaris Monitoring

## 📋 Descripción General

Implementación de **MQTT ingesta** como segundo canal de entrada de lecturas para dispositivos IoT con batería limitada. Complementa el canal HTTP existente, permitiendo que dispositivos ESP32 u otros clientes MQTT publiquen lecturas directamente al broker HiveMQ Cloud.

**Deadline:** 15 septiembre 2026 18:00 (Could have - no merge si no está en verde)

---

## 🎯 Criterios de Aceptación (Todos Implementados ✅)

| # | Criterio | Estado | Evidencia |
|---|----------|--------|-----------|
| 1 | ADR-0002 documenta decisión de broker MQTT | ✅ | [docs/adr/ADR-0002-mqtt-broker.md](../adr/ADR-0002-mqtt-broker.md) |
| 2 | Variables MQTT en .env.example y render.yaml | ✅ | MQTT_HOST, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD |
| 3 | MQTTAdapter implementado con patrón SOLID | ✅ | [src/utils/mqtt_adapter.py](../../src/utils/mqtt_adapter.py) |
| 4 | Lifespan event en FastAPI para startup/shutdown | ✅ | [src/main.py](../../src/main.py#L35-L62) |
| 5 | /health reporta estado MQTT (connected/disconnected/disabled) | ✅ | [src/utils/routers/health.py](../../src/utils/routers/health.py#L30) |
| 6 | Payload inválido no tumba suscriptor | ✅ | Error handling resiliente con logging |
| 7 | Lectura con eficiencia y anomalía calculadas | ✅ | Reutiliza ReadingService.create() |
| 8 | Tests sin broker real en CI | ✅ | [tests/unit/test_mqtt_adapter.py](../../tests/unit/test_mqtt_adapter.py) |
| 9 | Documentación ESP32 con PubSubClient | ✅ | [docs/ESP32_INTEGRATION.md](../ESP32_INTEGRATION.md#canal-mqtt) |
| 10 | Cobertura ≥90%, ruff y mypy limpios | ✅ | Coverage 93.28%, 152 tests passed |

---

## 🔧 Cambios Realizados

### 1. Configuración y Dependencias
- **requirements.txt**: Agregado `paho-mqtt==1.6.1`
- **requirements-dev.txt**: Incluye herramientas de validación (ruff, mypy, pytest)
- **.env.example**: Variables MQTT (MQTT_HOST, MQTT_PORT, MQTT_USERNAME, MQTT_PASSWORD, MQTT_TOPIC)
- **render.yaml**: Configuración con `sync: false` para credenciales de Render

### 2. Adaptador MQTT
**Archivo:** `src/utils/mqtt_adapter.py` (169 líneas)

**Clase:** `MQTTAdapter`
- Constructor: Inicializa con `Settings` y `db_session_factory`
- `enabled`: Booleano basado en presencia de `MQTT_HOST`
- `status`: Estados (disabled, connecting, connected, disconnected)
- `_extract_cell_id_from_topic()`: Parsea `solaris/cells/{cell_id}/readings`
- `_on_connect()`, `_on_disconnect()`, `_on_message()`: Callbacks MQTT
- `connect()`: Conexión blocking (corre en thread daemon)
- `disconnect()`: Desconexión graceful
- `get_status()`: Retorna estado actual

**Características:**
- Valida payload con `ReadingCreate` schema
- Inyecta en `ReadingService.create()` (sin duplicar lógica)
- Manejo resiliente: payload inválido se loguea y continúa
- TLS habilitado para HiveMQ Cloud (puerto 8883)
- Reutiliza `SqlAlchemyReadingRepository`, `SqlAlchemyCellRepository`, `ReadingAnalyzer`

### 3. Integración FastAPI
**Archivo:** `src/main.py`

**Cambios:**
- Importa `AsyncGenerator` de `collections.abc`
- Importa `MQTTAdapter` y `threading`
- Variables globales: `_mqtt_adapter: MQTTAdapter | None`
- Función `get_mqtt_adapter()`: Getter para acceso desde routers
- Decorador `@asynccontextmanager` en `lifespan(app: FastAPI)`
  - Startup: Crea `MQTTAdapter`, inicia en thread daemon si enabled
  - Shutdown: Llama `disconnect()` para graceful close

**Beneficio:** MQTT connection se maneja de forma lifecycle-aware sin bloquear startup

### 4. Health Endpoint
**Archivo:** `src/utils/routers/health.py`

**Cambios:**
- Importa `get_mqtt_adapter()` desde main
- Agrega campo `mqtt_status` en respuesta `/health`
- Retorna: "disabled", "connecting", "connected", o "disconnected"

**Ejemplo de respuesta:**
```json
{
  "status": "operational",
  "mqtt_status": "connected",
  "timestamp": "2026-09-14T10:00:00Z",
  "cell_count": 5,
  "latest_reading": "2026-09-14T09:55:00Z"
}
```

### 5. Tests Unitarios
**Archivo:** `tests/unit/test_mqtt_adapter.py` (168 líneas, 12 test cases)

**Cobertura:**
- Inicialización con/sin MQTT_HOST
- Extracción de cell_id desde topic válido/inválido
- Callbacks de conexión (success/failure/disconnect)
- Manejo de mensajes:
  - Payload JSON válido
  - JSON malformado
  - Topic inválido
  - Campos requeridos faltantes
- Status retrieval

**Mocking:**
- Cliente MQTT mockado (sin broker real en CI)
- `ReadingService` mockado
- Base de datos con fixtures

### 6. Documentación
**Archivos modificados:**

a) **docs/ESP32_INTEGRATION.md** - Nueva sección "Canal MQTT (Alternativa de Bajo Consumo)"
   - Configuración HiveMQ Cloud
   - Código Arduino completo con PubSubClient
   - Formato de payload JSON
   - Tabla comparativa: HTTP vs MQTT (energía, batería, latencia)
   - Verificación con mosquitto_pub
   - Topic pattern: `solaris/cells/{cell_id}/readings`

b) **docs/adr/ADR-0002-mqtt-broker.md**
   - Estado: Aceptado
   - Contexto: Dispositivos IoT con batería, Render no soporta TCP
   - Decisión: HiveMQ Cloud Serverless + TLS 8883
   - Patrón SOLID: Reutiliza schemas y services
   - Alternativas descartadas: Self-hosted en Render

### 7. Prompts AI Documentados
**Archivo:** `docs/ai_logs/AI_LOG_Lyla.md`

Agregados 4 prompts con documentación completa:
- **Prompt #40**: MQTT adapter implementation con FastAPI lifespan
- **Prompt #41**: Unit tests sin broker real
- **Prompt #42**: Validación final y coverage
- **Prompt #43**: Code quality y dependencias

---

## ✅ Validación Final

### Code Quality
```
✅ Ruff check: All checks passed
✅ Ruff format: 49 files already formatted
✅ Mypy: Success - no issues found in 47 source files
✅ pytest: 152 tests passed (93.28% coverage, exceeds 90%)
```

### Test Results
```
Integration Tests:  32 tests
Unit Tests:        120 tests (incluyendo 12 MQTT adapter)
Smoke Tests:         2 tests
─────────────────────────────────
Total:             152 tests PASSED ✅
```

### Coverage por Módulo
- src/db.py: 100%
- src/utils/domain/: 100%
- src/utils/repositories/: 100%
- src/utils/routers/cells.py: 100%
- src/utils/routers/health.py: 100%
- src/utils/routers/readings.py: 100%
- src/utils/services/: 100%
- **src/utils/mqtt_adapter.py: 68.81%** (expected - connect() con TLS real no se prueba en CI)

**Total Coverage: 93.28%**

---

## 🚀 Deployment

### Configuración en Render

Agregadas variables de entorno (manual en console, no en repo):
```
MQTT_HOST=tu-cluster.hivemq.cloud
MQTT_PORT=8883
MQTT_USERNAME=tu_usuario
MQTT_PASSWORD=tu_password
MQTT_TOPIC=solaris/cells/+/readings
```

**Nota:** `sync: false` en render.yaml previene que credenciales se sincronicen desde el repo.

### Verificación Post-Deployment

```bash
# 1. Verificar que /health reporta MQTT connected
curl https://api.solaris-monitoring.com/health | jq .mqtt_status

# 2. Publicar test reading
mosquitto_pub -h tu-cluster.hivemq.cloud -p 8883 \
  -u tu_usuario -P tu_password \
  -t "solaris/cells/1/readings" \
  -m '{"voltage_measured": 4.85, "timestamp": "2026-09-14T10:00:00Z"}'

# 3. Verificar que llegó a la API
curl https://api.solaris-monitoring.com/api/v1/readings | jq '.[-1]'
```

---

## 📊 Arquitectura

```
Dispositivo IoT (ESP32)
        ↓ MQTT (TLS 8883)
    HiveMQ Cloud
        ↓
    MQTTAdapter
        ↓
    ReadingCreate (Pydantic validation)
        ↓
    ReadingService.create()
        ↓
    Database (PostgreSQL en prod)
```

**SOLID Principles Applied:**
- ✅ Single Responsibility: MQTTAdapter = input channel specialization
- ✅ Open/Closed: Adaptable para otros brokers sin cambiar core logic
- ✅ Liskov Substitution: ReadingService.create() es agnóstico del origen
- ✅ Interface Segregation: Callbacks MQTT separados y especializados
- ✅ Dependency Injection: db_session_factory inyectado en constructor

---

## 🔒 Seguridad

- ✅ TLS 1.2+ habilitado en puerto 8883
- ✅ Username/password para autenticación MQTT
- ✅ Payload validado con Pydantic (ReadingCreate)
- ✅ Topic parsing validado (solo `solaris/cells/{id}/readings`)
- ✅ Cell ID validation: solo células activas aceptan readings
- ✅ Timestamp validation: rechaza readings del futuro (clock tolerance ±5 min)

---

## 📈 Performance

| Métrica | HTTP | MQTT |
|---------|------|------|
| Consumo energía | Alto | Muy bajo |
| Latencia | Media | Baja |
| Batería (5 min intervalo) | ~1 día | ~1 semana |
| Payload size | ~150 bytes | ~120 bytes |
| Overhead TLS | Sí | Sí (8883) |

**Ideal para:** Dispositivos remotos, conexión intermitente, batería limitada.

---

## 📝 Commits Relacionados

```
993e4a9 style: Apply ruff formatting to MQTT adapter and related files
b1825f0 docs: Add AI log Prompt #43 for code quality and dependencies
c6d4a03 fix: Code quality and type safety validation for MQTT adapter
4e15f17 feat: Implement MQTT adapter as IoT input channel (Step 3)
3903f13 docs: Add AI logs Prompts #40-#42 for MQTT implementation
```

---

## 🎓 Cómo Usar

### Para ESP32 con Arduino IDE

1. Instalar librería `PubSubClient` vía Arduino IDE
2. Copiar código de [docs/ESP32_INTEGRATION.md](../ESP32_INTEGRATION.md#código-esp32-con-pubsubclient)
3. Configurar credenciales MQTT
4. Upload al dispositivo

### Para Devices Existentes (HTTP)

Sin cambios. Seguir usando POST `/api/v1/readings` con X-API-Key.

### Para Monitoreo

- GET `/health` → Ver `mqtt_status`
- GET `/api/v1/readings` → Lecturas de cualquier canal (HTTP o MQTT)

---

## ✨ Beneficios

1. **Flexibilidad**: HTTP y MQTT coexisten, cliente elige basado en sus capacidades
2. **Eficiencia**: IoT devices ahorran energía usando MQTT
3. **Escalabilidad**: Broker cloud maneja desconexiones automáticas
4. **Confiabilidad**: Payload inválido no tumba suscriptor, logging completo
5. **Facilidad**: Reutiliza toda la lógica de cálculo (eficiencia, anomalía)
6. **Documentación**: Ejemplos completos y ADR decisional

---

## 🔍 Testing

Todos los tests corren sin broker MQTT real (CI-friendly):
- Mocks en `unittest.mock`
- Database session factory mockada
- No requiere credenciales externas

Producción: Broker real HiveMQ Cloud

---

## ❓ FAQ

**¿Qué pasa si MQTT_HOST no está definido?**
- API arranca sin MQTT, `mqtt_status: "disabled"` en /health
- HTTP sigue siendo funcional

**¿Puedo usar otro broker MQTT?**
- Sí, solo cambiar MQTT_HOST y credenciales
- MQTTAdapter es agnóstico del broker

**¿Qué pasa si el payload es inválido?**
- Se loguea WARNING y se descarta
- Suscriptor continúa escuchando
- No hay errores en logs de aplicación

**¿Cobertura de mqtt_adapter es baja (68.81%)?**
- Sí, porque `connect()` con TLS real y loop_forever() no se mockan en tests
- Es expected - las líneas no testeadas son la conexión TLS real y loop blocking

---

**Preparado para merge a `main` cuando se apruebe.** Todos los criterios de aceptación implementados y validados. ✅
