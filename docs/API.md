# API REST — EDSIA Beyond Photovoltaic Monitor

API para registrar lecturas de voltaje de celdas fotovoltaicas enviadas por dispositivos IoT
(ESP32) y consultar su eficiencia.

- **Base URL local:** `http://localhost:8000`
- **Swagger UI:** `/docs` · **ReDoc:** `/redoc` · **OpenAPI:** `/openapi.json`

---

## Reglas de negocio

| Regla | Detalle |
|---|---|
| Eficiencia | `(voltage_measured / rated_voltage) * 100`, redondeada a 2 decimales |
| Límite seguro | `max_safe_voltage = rated_voltage * 1.2`. Lo **deriva el servidor**; no se envía |
| Anomalía | Se marca si `voltage_measured > max_safe_voltage` **o** `eficiencia < efficiency_threshold` |
| Timestamps | Siempre UTC. Un valor sin zona horaria se interpreta como UTC |
| Reloj del dispositivo | Se tolera una deriva de hasta 5 minutos hacia el futuro; más allá se rechaza |
| Celda inactiva | No acepta lecturas nuevas |
| Borrado | Eliminar una celda elimina sus lecturas en cascada |

---

## Salud

### `GET /`
```json
{ "message": "EDSIA Beyond API - Photovoltaic Monitor" }
```

### `GET /health`
```json
{ "status": "ok", "message": "API funcionando correctamente" }
```

---

## Celdas fotovoltaicas

### `POST /api/v1/cells` → `201`

```json
{
  "name": "Celda_01",
  "location": "Techo Norte",
  "rated_voltage": 5.0,
  "efficiency_threshold": 80.0
}
```

Respuesta:

```json
{
  "id": 1,
  "name": "Celda_01",
  "location": "Techo Norte",
  "rated_voltage": 5.0,
  "max_safe_voltage": 6.0,
  "efficiency_threshold": 80.0,
  "is_active": true
}
```

| Campo | Reglas |
|---|---|
| `name` | Requerido, único, 1–100 caracteres |
| `location` | Requerido, 1–200 caracteres |
| `rated_voltage` | Requerido, `> 0` |
| `efficiency_threshold` | Opcional, 0–100 (por defecto `80.0`) |

Errores: `409` si el nombre ya existe · `422` si el payload es inválido.

### `GET /api/v1/cells` → `200`
Lista todas las celdas.

### `GET /api/v1/cells/active` → `200`
Lista sólo las celdas con `is_active = true`.

### `GET /api/v1/cells/{cell_id}` → `200`
Errores: `404` si no existe.

### `PUT /api/v1/cells/{cell_id}` → `200`

Actualización parcial; sólo se modifican los campos enviados.

```json
{ "rated_voltage": 10.0, "is_active": false }
```

Cambiar `rated_voltage` **recalcula** `max_safe_voltage`.

Errores: `404` si no existe · `409` si el nombre pertenece a otra celda.

### `DELETE /api/v1/cells/{cell_id}` → `204`
Elimina la celda y sus lecturas. Errores: `404` si no existe.

---

## Lecturas de voltaje

### `POST /api/v1/readings` → `201`

Endpoint que consume el ESP32.

```json
{
  "cell_id": 1,
  "voltage_measured": 4.85,
  "timestamp": "2026-09-11T14:30:00Z"
}
```

`timestamp` es opcional: si se omite, el servidor usa la hora UTC de recepción.

Respuesta:

```json
{
  "id": 42,
  "cell_id": 1,
  "voltage_measured": 4.85,
  "efficiency_percentage": 97.0,
  "is_anomaly": false,
  "timestamp": "2026-09-11T14:30:00Z",
  "created_at": "2026-09-11T14:30:01.123456Z"
}
```

Errores: `404` si la celda no existe · `409` si la celda está inactiva ·
`422` si `voltage_measured <= 0` o el timestamp está en el futuro.

### `GET /api/v1/readings?limit=100` → `200`
Más recientes primero. `limit` entre 1 y 1000 (por defecto 100).

### `GET /api/v1/readings/{reading_id}` → `200`
Errores: `404` si no existe.

### `GET /api/v1/readings/cell/{cell_id}?limit=100` → `200`
Lecturas de una celda, más recientes primero. Errores: `404` si la celda no existe.

### `GET /api/v1/readings/cell/{cell_id}/summary?days=7` → `200`

```json
{
  "cell_id": 1,
  "cell_name": "Celda_01",
  "period_days": 7,
  "reading_count": 144,
  "avg_voltage": 4.87,
  "max_voltage": 5.0,
  "min_voltage": 4.5,
  "avg_efficiency": 97.4,
  "anomaly_count": 2
}
```

`days` entre 1 y 365 (por defecto 7).

Errores: `404` si la celda no existe o no tiene lecturas en el período.

---

## Códigos de estado

| Código | Significado |
|---|---|
| `200` | Consulta exitosa |
| `201` | Recurso creado |
| `204` | Eliminación exitosa (sin cuerpo) |
| `404` | Recurso inexistente o período sin datos |
| `409` | Conflicto: nombre duplicado o celda inactiva |
| `422` | Payload inválido |

Los errores devuelven `{"detail": "<mensaje>"}`.

---

## Ejemplos

```bash
# Registrar una celda
curl -X POST http://localhost:8000/api/v1/cells \
  -H "Content-Type: application/json" \
  -d '{"name":"Celda_01","location":"Techo","rated_voltage":5.0}'

# Enviar una lectura (lo que hace el ESP32)
curl -X POST http://localhost:8000/api/v1/readings \
  -H "Content-Type: application/json" \
  -d '{"cell_id":1,"voltage_measured":4.85}'

# Consultar el resumen de los últimos 7 días
curl http://localhost:8000/api/v1/readings/cell/1/summary?days=7
```
