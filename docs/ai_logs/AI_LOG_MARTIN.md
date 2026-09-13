# Log de prompts a las IAs

* Nombre de integrante - Prompt # (# de prompt)
* IA utilizada
* Prompt del integrante completo
* Respuesta de la IA completa
* Qué se aceptó
* Qué se denegó
* Qué se modificó

---

# Lyla Alice - Prompt #1

### IA utilizada: Claude haiku 4.5

**Prompt del integrante completo:**
> Te voy a dar acceso a una carpeta que contiene 4 proyectos en total.
>Detalle de los proyectos:

>* 3 proyectos de SensorHub: Son implementaciones de una API (una versión es mía y las otras dos son de mis compañeros de equipo).
>* 1 proyecto llamado EDSIA-BEYOND: Este es un proyecto nuevo que vamos a desarrollar en conjunto. Para este caso en particular, aún no tenemos las métricas definidas, pero nuestro objetivo actual es empezar a estructurar las partes del sistema que queremos automatizar.

>Instrucción estricta: Por ahora, tu única tarea es leer, analizar y comprender la arquitectura y relación entre estos repositorios. No quiero que realices, propongas ni apliques ningún cambio al código ni a la estructura.
>Solo confirma que has procesado el contexto de los 4 proyectos y dime que estás listo para mis siguientes instrucciones.

**Respuesta de la IA completa:**

```bash
Los 3 SensorHub (mismo dominio, implementaciones independientes)

Los tres son APIs REST en Python + FastAPI + SQLAlchemy 2.x + Alembic, con PostgreSQL en producción y SQLite en local/tests, dockerizadas y desplegadas en Render. Comparten el mismo dominio: Sensor → Reading → Alert (sensores que emiten lecturas, que disparan alertas por umbral con máquina de estados open → acknowledged → resolved), y arquitectura en capas (routers/services/repositories/models) documentada con ADRs. Todo apunta a que nace del mismo curso (SDLC/electrónica) resuelto por cada integrante por separado.

EDSIA-BEYOND

Repositorio en puro scaffolding: casi todo vacío (pyproject.toml, requirements.txt sin contenido), sin código ni arquitectura definida aún. Es Python por convención (.gitignore), sin framework elegido. Lo único con sustancia es CONTRIBUTING.md (en la rama dev remota): flujo main protegido + dev de integración, 2 revisores obligatorios, cobertura mínima 90%, y regla de que todo el código vive en src/. El AI_LOG.md de esa misma rama confirma que la intención explícita del equipo es analizar los 3 SensorHub existentes para repartir roles de cara a EDSIA-BEYOND — es decir, este nuevo proyecto probablemente reutilizará patrones/aprendizajes de esas tres implementaciones (posiblemente una consolidación o evolución del mismo dominio de sensores, aunque eso aún no está definido).

```

**Qué se aceptó:** N/A.

**Qué se denegó:** N/A.

**Qué se modificó:** N/A.

---

# Lyla Alice - Prompt #2

### IA utilizada: Claude haiku 4.5

**Prompt del integrante completo:**
> Ahora que tienes el contexto de los 4 proyectos, quiero que trabajemos en el proyecto EDSIA-BEYOND.
>Tu tarea es generar e integrar los archivos necesarios para implementar un pipeline de Integración Continua (CI) utilizando GitHub Actions.
>Requerimientos específicos:

>1. Toma como base lo existente: Analiza y reutiliza la estructura de los pipelines de GitHub Actions que ya tenemos configurados en los 3 proyectos de SensorHub.
>2. Umbral de cobertura: El nuevo pipeline debe estar configurado para exigir una cobertura de pruebas (coverage) mínima estricta del 90%. Si no se alcanza, el pipeline debe fallar.
>3. Propuesta de mejoras: Además de replicar y adaptar lo que ya tenemos, quiero que analices nuestra configuración actual de CI y me propongas mejoras, optimizaciones o mejores prácticas que podríamos aplicar en este nuevo pipeline para EDSIA-BEYOND (por ejemplo, en temas de caché, tiempos de ejecución, o seguridad).

>Entrégame los archivos de configuración de GitHub Actions resultantes (ej. el archivo `.yml`) y la lista de las mejoras propuestas para que las discutamos.

**Respuesta de la IA completa:**

```bash
Archivos entregados

En EDSIA-BEYOND/EDSIA-Beyond, estás en la rama dev_martin (aún sin commitear, para que revises antes):

EDSIA-BEYOND/EDSIA-Beyond/.github/workflows/ci.yml — el pipeline CI
EDSIA-BEYOND/EDSIA-Beyond/pyproject.toml — config de ruff/mypy/pytest/coverage (fuente única del umbral 90%)
EDSIA-BEYOND/EDSIA-Beyond/requirements-dev.txt — deps de CI con versión fijada
EDSIA-BEYOND/EDSIA-Beyond/src/edsia_beyond/__init__.py + EDSIA-BEYOND/EDSIA-Beyond/tests/test_smoke.py — andamiaje mínimo (respeta la regla del CONTRIBUTING.md de "todo el código vive en src/") para que el pipeline corra en verde desde el primer commit en vez de fallar por falta de estructura

Lo validé localmente: ruff check, ruff format --check, mypy src y pytest --cov=src (100% cobertura sobre el andamiaje vacío, umbral 90% cumplido) — todo pasa.

Qué tomé de los 3 SensorHub y qué cambié

Los tres pipelines de SensorHub son casi idénticos: checkout → setup-python → pip install sueltos → ruff → mypy → pytest --cov=app --cov-fail-under=N (80/80/95 según el repo). Reutilicé esa columna vertebral, pero apliqué directamente estas mejoras (de bajo riesgo, no arquitectónicas):

Umbral centralizado: en vez de un --cov-fail-under=N hardcodeado y distinto en cada repo, el 90% vive en pyproject.toml ([tool.coverage.report] fail_under) — una sola fuente de verdad versionada.
Deps de CI fijadas (requirements-dev.txt con versión exacta) en vez de pip install pytest ruff mypy sin pin en cada corrida — evita que un release nuevo de una herramienta rompa el CI sin aviso.
Cache de pip (patrón que ya usa CherryStraw, ausente en tu repo y el de José).
ruff format --check además de ruff check — ninguno de los tres valida formato, solo lint.
Triggers en main y dev (los 3 SensorHub solo corren en main; EDSIA-BEYOND sí tiene dev como rama de integración real).
concurrency para cancelar corridas obsoletas del mismo PR/rama (ahorra minutos de Actions).
Artefacto de coverage (coverage.xml subido con upload-artifact) para trazabilidad, ausente en los tres.
Mejoras propuestas para discutir (no aplicadas todavía)
Escaneo de dependencias/vulnerabilidades: CherryStraw usa Trivy sobre imagen Docker, pero EDSIA-BEYOND todavía no tiene Dockerfile. Propongo pip-audit (puro Python, sin Docker) ahora, y migrar a Trivy cuando exista imagen.
Auto-crear Issue en fallo de main (patrón de CherryStraw) — útil pero puede ser ruidoso en equipo de 3; decidir si aplica solo a main o también a dev.
Separar en jobs paralelos (lint / types / tests) en vez de un job secuencial — feedback más rápido y falla más clara, a cambio de más minutos de runner y YAML más complejo.
pre-commit para correr ruff/mypy en local antes del push y reducir CI en rojo.
Dependabot para mantener actualizadas las versiones fijadas en requirements-dev.txt.
CODEOWNERS: el CONTRIBUTING.md exige 2 aprobaciones por PR, pero eso hoy es solo texto — GitHub no lo fuerza sin este archivo + branch protection configurada en Settings (fuera del alcance de un .yml).
Reservar workflows tipo uptime.yml / deploy-production.yml (CherryStraw) para cuando exista un servicio desplegable real — prematuros ahora mismo.
```

**Qué se aceptó:** Se acepto la carpeta de ci con la configuracion realizada.

**Qué se denegó:** Se denego por ahora los otros archivos generados.

**Qué se modificó:** Se modifico una parte del ci que tambien afectaba a otras ramas, solo debe ser a main.


---