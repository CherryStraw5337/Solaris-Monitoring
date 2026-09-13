# Guía de Deployment - Solaris Monitoring API

## Desarrollo Local con Docker

### Requisitos Previos
- Docker y Docker Compose instalados
- Python 3.12+ (para desarrollo sin Docker)
- Git

### Levantar Ambiente Local

```bash
# 1. Clonar repositorio
git clone <repository-url>
cd Solaris-Monitoring

# 2. Crear archivo .env
cp .env.example .env

# 3. Levantar servicios con Docker Compose
docker-compose up -d

# 4. Verificar salud de la API
curl http://localhost:8000/health

# 5. Acceder a Swagger UI
open http://localhost:8000/docs
```

### Detener Ambiente

```bash
docker-compose down
```

### Ver Logs

```bash
# Logs de API
docker-compose logs -f api

# Logs de BD
docker-compose logs -f db

# Logs de servicio específico
docker-compose logs -f <service_name>
```

---

## Desarrollo Sin Docker

### Instalación Inicial

```bash
# 1. Crear virtual environment
python -m venv venv

# 2. Activar venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear .env
cp .env.example .env
```

### Ejecutar Localmente

```bash
# Modo desarrollo (auto-reload)
uvicorn main:app --app-dir src --reload --host 0.0.0.0 --port 8000
```

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Con reporte de cobertura
pytest --cov=src --cov-report=html

# Tests específicos
pytest tests/test_cells.py -v
```

---

## Producción en Render.com

### Paso 1: Conectar Repositorio a Render

1. Ir a [render.com](https://render.com)
2. Crear nueva cuenta o iniciar sesión
3. Click en **New** → **Web Service**
4. Conectar repositorio GitHub

### Paso 2: Configurar el Servicio

1. Seleccionar rama: `main`
2. Runtime: **Docker**
3. Plan: **Starter** (o gratuito si aplica)
4. Health Check Path: `/health`

### Paso 3: Crear Base de Datos PostgreSQL

1. Click en **New** → **PostgreSQL**
2. Nombre: `solaris-monitoring-db`
3. Plan: **Starter**
4. Render generará automáticamente `DATABASE_URL`

### Paso 4: Configurar Variables de Entorno

En la dashboard de Render, bajo "Environment":

```
ENVIRONMENT=production
DEBUG=False
```

La `DATABASE_URL` se inyecta automáticamente desde la BD.

### Paso 5: Deploy

```bash
# Push a main dispara deploy automático
git push origin main
```

Monitorear progreso en Render Dashboard.

### Acceder a API en Producción

```
https://solaris-monitoring-api.onrender.com/health
https://solaris-monitoring-api.onrender.com/docs
```

---

## CI/CD con GitHub Actions

El repositorio incluye pipeline `.github/workflows/ci-cd.yml` que:

1. **Executa tests** en cada push
2. **Valida código** con Ruff + mypy
3. **Genera cobertura** de código
4. **Construye imagen Docker** en main

### Verificar Status

```bash
# En GitHub, ir a Actions tab para ver runs
```

---

## Variables de Entorno (Producción)

```env
# Obligatorias
DATABASE_URL=postgresql+psycopg://user:pass@host:5432/db

# Opcionales
ENVIRONMENT=production
DEBUG=False
API_TITLE=Solaris Monitoring - Photovoltaic Monitor
API_VERSION=1.0.0
```

---

## Migraciones de Base de Datos

### Crear Nueva Migración

```bash
# Con Docker
docker-compose exec api alembic revision --autogenerate -m "Descripción del cambio"

# Sin Docker
alembic revision --autogenerate -m "Descripción del cambio"
```

### Aplicar Migraciones

```bash
# Automático en startup (incluido en CMD del Dockerfile)
alembic upgrade head
```

---

## Monitoreo en Producción

### Health Check

```bash
curl https://solaris-monitoring-api.onrender.com/health
```

Debe retornar:
```json
{"status": "ok", "message": "API funcionando correctamente"}
```

### Logs en Render

1. Ir a Web Service dashboard
2. Click en **Logs**
3. Ver output en tiempo real

### Métricas

- Dashboard de Render muestra CPU, memoria, requests/segundo
- Status page muestra uptime

---

## Troubleshooting

### Error: "Database connection refused"

```bash
# Verificar que PostgreSQL está corriendo
docker-compose ps

# Reiniciar BD
docker-compose restart db
```

### Error: "Alembic revision error"

```bash
# Inicializar Alembic
alembic init alembic

# Confirmar alembic.ini tiene pythonpath correcto
```

### Error: "Port 8000 already in use"

```bash
# Encontrar qué está usando el puerto
lsof -i :8000

# Liberar puerto
kill -9 <PID>
```

### API lenta en Producción

1. Revisar logs en Render
2. Aumentar workers: `--workers 8`
3. Optimizar queries de BD
4. Aumentar plan de Render si es CPU-bound

---

## Rollback

Si hay problema en producción:

```bash
# Revertir a commit anterior
git revert <commit-hash>
git push origin main

# O crear hotfix branch
git checkout -b hotfix/issue-name main
# ... arreglar issue ...
git push origin hotfix/issue-name
# Abrir PR a main
```

Render redeploya automáticamente en cada push a main.

---

## Backup de Base de Datos

Render maneja backups automáticos. Para exportar manualmente:

```bash
# Conexión remota a DB
PGPASSWORD=password pg_dump -h host -U user -d database > backup.sql

# Restaurar
psql -h host -U user -d database < backup.sql
```
