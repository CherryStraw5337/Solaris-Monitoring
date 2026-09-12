# AI Development Log - EDSIA Beyond API

## Sesión 1: Planificación y Arquitectura (2026-09-11)

### Objetivos
- Definir arquitectura de API REST para monitoreo de celdas fotovoltaicas
- Crear plan de acción con Docker y deploy en Render
- Considerar integración con ESP32 (IoT)

### Decisiones Tomadas

1. **Stack Tecnológico**
   - FastAPI (framework moderno, tipo seguro)
   - SQLAlchemy 2.x + Alembic (ORM profesional)
   - PostgreSQL en producción / SQLite en desarrollo
   - Python 3.12+ (features modernas)

2. **Arquitectura**
   - Patrón por capas: Routers → Services → Repositories → DB
   - Schemas Pydantic para validación
   - Inyección de dependencias con FastAPI

3. **Infraestructura**
   - Docker multi-stage (optimización de imagen)
   - Docker Compose para desarrollo
   - GitHub Actions para CI/CD
   - Render.com para hosting (similar a api-jose)

4. **Testing**
   - pytest con >90% cobertura
   - Conftest.py para fixtures compartidas
   - Tests de integración HTTP

### Lecciones de Otras APIs

Analizamos `api-jose` (SensorHub) para seguir patrones consistentes:
- Estructura de directorios (models, repositories, routers)
- Dockerfile multi-stage
- docker-compose.yml con servicios acoplados
- render.yaml para deployments automáticos
- GitHub Actions básicos

### Entregables Completados

✅ Plan de acción detallado (Fase 1-9)  
✅ Estructura de directorios  
✅ Dockerfile multi-stage  
✅ docker-compose.yml (dev)  
✅ render.yaml (prod)  
✅ Modelos SQLAlchemy  
✅ Schemas Pydantic  
✅ Repositories (CRUD)  
✅ Services (lógica de negocio)  
✅ Routers (endpoints)  
✅ Tests básicos  
✅ GitHub Actions  
✅ Documentación (API, DEPLOYMENT, ESP32)  

---

## Sesión 2: Implementación Base (En Progreso)

### Tareas Completadas

- [x] Crear estructura base del proyecto
- [x] Configurar Docker Compose
- [x] Implementar modelos PhotovoltaicCell y Reading
- [x] Crear schemas de validación
- [x] Implementar repositories (CRUD operations)
- [x] Crear servicios con lógica de negocio
- [x] Construir routers para células y lecturas
- [x] Escribir tests de integración
- [x] Documentación completa
- [ ] Ejecutar en local con Docker
- [ ] Validar todos los tests pasan
- [ ] Deploy en Render (próximas sesiones)

### Decisiones Técnicas

1. **Eficiencia Calculada Automáticamente**
   - Se calcula en `ReadingService.create_reading()`
   - Fórmula: `(voltage_measured / rated_voltage) * 100`

2. **Detección de Anomalías**
   - Automática en lectura
   - Criterio: `voltage > max_safe_voltage` (120% del nominal)
   - Permite análisis posterior en dashboard

3. **Timestamps**
   - ISO 8601 con UTC (Z suffix)
   - Campo `timestamp` para hora de lectura (ESP32)
   - Campo `created_at` para hora de almacenamiento (API)

4. **max_safe_voltage**
   - Se calcula automáticamente al crear celda
   - Valor: `rated_voltage * 1.2`
   - Protege contra lecturas erróneas de sensores

### Próximos Pasos

1. **Testing en Local**
   ```bash
   docker-compose up -d
   docker-compose exec api pytest
   ```

2. **Validación de Datos**
   - Probar con curl todos los endpoints
   - Verificar validaciones de Pydantic
   - Probar anomalías

3. **Alembic Migrations**
   - Inicializar Alembic
   - Generar migración inicial
   - Probar upgrade/downgrade

4. **Dashboard (Futuro)**
   - Endpoint de analytics
   - Agregaciones por período
   - Gráficos de eficiencia

### Issues Potenciales Identificados

- [ ] Timezone en PostgreSQL (puede haber drift con UTC)
- [ ] Límites de ingesta (¿cuántas lecturas por segundo?)
- [ ] Autenticación (ESP32 necesita API Key?)
- [ ] Retención de datos (¿eliminar lecturas antiguas?)

### Cambios Futuros Potenciales

1. Agregar autenticación JWT para endpoints sensibles
2. Implementar rate limiting por celda
3. Agregar alertas cuando eficiencia < threshold
4. Crear endpoint de agregación por período (día/semana/mes)
5. Implementar soft deletes para auditoría

---

## Notas Técnicas

### Por qué SQLAlchemy 2.x

- Type hints nativos
- SQL type-safe expressions
- API moderna y consistente
- Excelente con FastAPI

### Por qué Pydantic v2

- Validación rápida (Rust)
- Serialización JSON optimizada
- Type hints integrados
- Compatible con OpenAPI

### Patrón por Capas

```
API Request
    ↓
Router (endpoint, validación HTTP)
    ↓
Service (lógica de negocio)
    ↓
Repository (acceso a datos)
    ↓
SQLAlchemy ORM
    ↓
PostgreSQL
```

Ventajas:
- Separación de responsabilidades
- Testeable (mock repositories)
- Reutilizable

---

## Recursos Consultados

- Documentación de FastAPI
- SQLAlchemy 2.x docs
- Patrones de `api-jose`
- PostgreSQL best practices
- Docker multi-stage optimization

## Próxima Sesión

- [ ] Ejecutar localmente
- [ ] Validar todos los tests
- [ ] Probar endpoints con Postman/curl
- [ ] Optimizar queries
- [ ] Preparar para deploy en Render
