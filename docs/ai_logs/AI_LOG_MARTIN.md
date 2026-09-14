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

# Martin Contreras - Prompt #3

### IA utilizada: Claude Haiku 4.5 (Claude Code)

**Prompt del integrante completo:**
> eres un programador senior encargado de desarrollar una API REST como las demas API que se encuentran en los distintos directorios. Para esta ocasion vamos a trabajar sobre edsia-beyond, pero es importante tomar contexto de las demas api.
> Para este reto vamos a trabajar en una API la cual sea la base para un sistema de control de eficiencia de celdas fotovoltaicas, las cuales serna celdas pequeñas las cuales se conectan a un esp32, simulando un sistema iot conectado a internet, este esp32 hara lecturas y hara request a la api en los cuales se guarde el valor de voltaje, que es el valor medido, se guarde la fecha y hora, para posteriormente si es posible hacer un dashboard el cual muestre un resumen de los datos obtenidos.
> Esto se hara tomando en cuenta el archivo pdf los cuales son las metricas del proyecto.
> Por ahora no hagas modificaciones, simplemente toma el contexto y si es posible genera un plan de accion.

**Respuesta de la IA (resumen):**
Revisó `api-jose` (FastAPI, SQLAlchemy, Alembic, repositorios, routers, Docker, Render) y el `pyproject.toml` de EDSIA-Beyond. Propuso un plan en capas (routers, services, repositories, models, schemas), dos modelos (`PhotovoltaicCell` y `Reading`), endpoints CRUD, la eficiencia calculada como `voltaje medido / voltaje nominal × 100` y 9 fases de trabajo.
**No pudo leer el PDF** porque faltaba `pdftoppm` en el equipo. Aun así entregó el plan y dejó "revisar el PDF" como pendiente.

**Alternativas consideradas:** Seguir el mismo patrón que `api-jose` o empezar con otra estructura. Se eligió el patrón conocido del curso.

**Validación:** Lectura manual del plan. No había código que ejecutar.

**Qué se aceptó:** La arquitectura en capas y el modelo de datos base.

**Qué se denegó:** Nada en este paso.

**Qué se modificó:** Se pidió agregar el despliegue con Docker (prompt #4).

**Criterio / lección:** El plan se armó **sin leer los lineamientos del PDF**. Detectamos ese hueco después: en el prompt #11 se leyó el PDF completo antes de definir las issues.

---

# Martin Contreras - Prompt #4

### IA utilizada: Claude Haiku 4.5 (Claude Code)

**Prompt del integrante completo:**
> ten en cuenta el deploy con docker

**Respuesta de la IA (resumen):**
Revisó el `Dockerfile`, el `docker-compose.yml` y el `render.yaml` de `api-jose`. Actualizó el plan con un Dockerfile multi-stage, un `docker-compose` con PostgreSQL y healthcheck, un `render.yaml`, GitHub Actions y un flujo de despliegue.

**Alternativas consideradas:** Dockerfile de una sola etapa, como `api-jose`, contra uno multi-stage para reducir la imagen. Se eligió multi-stage.

**Validación:** Solo lectura del plan.

**Qué se aceptó:** El plan con Docker, Compose y Render.

**Qué se denegó:** Nada.

**Qué se modificó:** Nada.

---

# Martin Contreras - Prompt #6

### IA utilizada: Claude Opus 5 (Claude Code)

**Prompt del integrante completo:**
> revisa ahora la api rest, completa, haz los test con coverage mas de 90, al igual que ruff check y mypy, ademas de que siga solid y tambien tdd

**Respuesta de la IA (resumen):**
Antes de cambiar nada, corrió la suite existente: **fallaba**. Refactorizó la API y documentó los bugs que encontró:

- `PhotovoltaicCell.is_active is True` compara identidad en Python contra una columna, así que `list_active()` siempre devolvía vacío. Se corrigió con `.is_(True)`.
- Los tests con SQLite en memoria abrían una conexión nueva por hilo y encontraban la base vacía. Se resolvió con `StaticPool`.
- SQLite pierde la zona horaria. Se agregó el tipo `UTCDateTime`.
- El Dockerfile no tenía `PYTHONPATH` y su healthcheck usaba `requests`, que no era dependencia.
- El CMD ejecutaba `alembic upgrade head`, pero Alembic nunca se había configurado.
- Un nombre de celda duplicado daba 500; ahora da 409. Borrar una celda dejaba lecturas huérfanas.
- `efficiency_threshold` existía pero ningún código lo usaba.
- CORS con `*` combinado con credenciales, que los navegadores rechazan.
- Un `create_all` al importar el módulo creaba un `test.db` suelto.

Diseño SOLID aplicado:
- Dominio puro en `domain/analysis.py`: calculadora de eficiencia y detectores de anomalía intercambiables.
- Protocolos de repositorio (`CellLookup`, `CellRepository`, `ReadingRepository`).
- Servicios que reciben sus dependencias por constructor.
- `dependencies.py` como punto de composición.
- Manejadores de excepciones de dominio que devuelven 404 o 409.

**Alternativas consideradas:**
- `pydantic-settings` contra configuración con la librería estándar. Se usó la estándar para no agregar una dependencia que no estaba instalada.
- `passive_deletes=True` contra borrado en cascada desde el ORM. Se descartó el primero porque SQLite no aplica llaves foráneas por defecto y dejaría lecturas huérfanas.
- Crear tablas al arrancar contra migraciones de Alembic. Se eligió Alembic y se quitó la creación de tablas al importar.

**Validación:**
- 116 tests con **100 % de cobertura con ramas**; ruff y mypy limpios en `src` y `tests`.
- Migración generada y aplicada desde cero. **Falló la primera vez**, porque la migración importaba un tipo de la app; se corrigió con `render_item`.
- Servidor uvicorn real: se creó una celda, se enviaron lecturas normales y anómalas, se consultó el resumen y se probaron los errores 404 y 409.

**Honestidad sobre TDD:** el código ya existía, así que no fue TDD desde cero. Se partió de la suite en rojo y se escribieron los tests del comportamiento esperado antes de corregir. La IA lo declaró así en su respuesta.

**Qué se aceptó:** El refactor completo, que llegó a `main` en el commit *"feat: implement EDSIA Beyond backend"*.

**Qué se denegó:** Nada.

**Qué se modificó:** El equipo reorganizó después el paquete: `src/edsia_beyond/` pasó a `src/main.py`, `src/db.py` y `src/utils/` en *"feat: consolidar Solaris Monitoring"*.

**Detalle a revisar que señaló la IA:** en el working tree faltaban 3 archivos de la landing (`src/edsia_beyond/public/`). La IA no los había tocado: lo reportó y dio el comando para restaurarlos, sin restaurarlos por su cuenta.

---

# Martin Contreras - Prompt #7

### IA utilizada: Claude Opus 5 (Claude Code)

**Prompt del integrante completo:**
> en este caso, si quiero hacer el deploy en otro lado que no sea render como github pages, es popsible?

**Respuesta de la IA (resumen):**
Solo en parte. GitHub Pages sirve archivos estáticos y no puede ejecutar FastAPI, Alembic ni una base de datos. Propuso separar el dashboard (en Pages) de la API (en un servicio de contenedores) y advirtió dos cosas: la API necesita HTTPS y hay que limitar CORS al dominio de Pages.

**Alternativas consideradas:** GitHub Pages; Pages para el frontend junto con Render o otro servicio de contenedores para la API; un VPS con `docker compose`.

**Validación:** Razonamiento técnico, sin cambios de código.

**Qué se aceptó:** Mantener la API en Render.

**Qué se denegó:** Llevar la API a GitHub Pages.

**Qué se modificó:** Nada.

---

# Martin Contreras - Prompt #8

### IA utilizada: Claude Opus 5 (Claude Code)

**Prompt del integrante completo:**
> vuelve a checar mi rama, la actualice con mi rama main que modificaron anteriormente pero ahora no me deja abrir el swagger en local, me da estos errores:
> [se adjuntó el traceback de uvicorn, que termina en `ModuleNotFoundError: No module named 'solaris_monitoring'`]

**Respuesta de la IA (resumen):**
Tras el merge ya no existía el paquete `solaris_monitoring`: la app estaba en `src/main.py` y `src/utils/`. El código estaba bien; el error venía del comando de arranque documentado en `docs/DEPLOYMENT.md`. El comando correcto es `uvicorn main:app --app-dir src --reload`. Actualizó `DEPLOYMENT.md` y `CONTRIBUTING.md`.

**Alternativas consideradas:** Renombrar el código para que coincidiera con la documentación, o corregir la documentación. Se corrigió la documentación, que era la parte desactualizada.

**Validación:**
- Con el `venv` del proyecto, `/docs` respondió 200 con Swagger UI y `/openapi.json` listó 9 rutas.
- 117 tests pasaron.
- La IA detectó que el `venv` no tenía las dependencias de desarrollo y lo avisó.

**Qué se aceptó:** Las correcciones de documentación.

**Qué se denegó:** Nada.

**Qué se modificó:** Nada.

---

# Martin Contreras - Prompt #9

### IA utilizada: Claude Opus 5 (Claude Code)

**Prompt del integrante completo:**
> ahora que hice mi deploy en render me dijo esto:
> [se adjuntó el log de build y deploy de Render; la migración fallaba con `ModuleNotFoundError: No module named 'psycopg2'`]

**Respuesta de la IA (resumen):**
Render entrega `DATABASE_URL` como `postgresql://...` sin indicar el driver. En ese caso SQLAlchemy intenta cargar `psycopg2`, pero el proyecto instala `psycopg` versión 3. Agregó `normalize_database_url` en `src/utils/config.py`, que convierte `postgres://` y `postgresql://` en `postgresql+psycopg://`.

**Alternativas consideradas:**
1. Agregar `psycopg2-binary` a las dependencias: dos drivers para lo mismo.
2. Cambiar la URL a mano en Render: frágil, porque la variable viene enlazada a la base.
3. Normalizar la URL en la configuración. **Elegida**, porque cubre a la app y a Alembic en un solo lugar.

**Validación:**
- TDD: 6 tests nuevos, vistos en rojo antes de implementar.
- 123 tests con 100 % de cobertura; ruff y mypy limpios.
- Con el `venv`, que tiene las mismas dependencias que la imagen, una URL al estilo de Render cargó el driver `psycopg`.
- La IA aclaró que no pudo probar contra el PostgreSQL real de Render.

**Qué se aceptó:** El cambio, fusionado en `main` con el **PR #10** (*"Normalize PostgreSQL URLs for psycopg3 and update documentation"*).

**Qué se denegó:** Nada.

**Qué se modificó:** Nada.

---

# Martin Contreras - Prompt #10

### IA utilizada: Claude Opus 5 (Claude Code)

**Prompt del integrante completo:**
> revisa que se este haciendo el pre deploy y que se actualice todo con cada merge porque hice merge de una cosa que se encuentra en main pero no se actualizo en render

**Respuesta de la IA (resumen):**
Encontró dos problemas distintos:

1. **El deploy sí funcionaba, pero la landing nueva no se veía.** El PR #9 puso la landing en `src/public/`, mientras que `/` seguía sirviendo una copia vieja en `src/utils/public/`. Además, ninguna ruta entregaba el CSS, el JS ni la imagen. Se montó `src/public/` como archivos estáticos después de las rutas de la API y se eliminó la copia vieja.
2. **`render.yaml` no tenía pre-deploy ni rama definida.** Se agregaron `branch: main`, `autoDeployTrigger: commit`, `preDeployCommand: alembic upgrade head` y `dockerCommand`.

También agregó `commit` y `branch` a `/health` (con `RENDER_GIT_COMMIT` y `RENDER_GIT_BRANCH`) para comprobar qué versión está en línea.

**Alternativas consideradas:**
- `autoDeployTrigger: checksPass` (desplegar solo si pasa el CI). **Descartado:** los commits de versión que sube semantic-release usan `GITHUB_TOKEN`, que no dispara el CI. Nunca tendrían checks y Render dejaría de desplegar.
- Conservar las migraciones en el CMD del contenedor contra moverlas al pre-deploy. Se eligió el pre-deploy porque, si la migración falla, Render cancela el deploy y deja en línea la versión anterior.

**Validación:**
- La IA consultó la documentación oficial de Render antes de configurar. Confirmó que el pre-deploy funciona con Docker en planes de pago y que `render.yaml` solo se aplica a servicios creados desde un Blueprint.
- TDD con 131 tests: el test anterior de la portada pasaba precisamente porque se servía la página vieja, y se corrigió.
- Simulación local del deploy: se corrió `alembic upgrade head` y después uvicorn, y se verificaron la landing, sus archivos, `/docs`, la API y `/health`.
- Docker no se pudo probar porque el daemon no estaba activo; la IA lo informó.

**Qué se aceptó:** Todo.
**Qué se denegó:** Nada.

**Qué se modificó:** Nada.

---

# Martin Contreras - Prompt #12

### IA utilizada: Claude Opus 5 (Claude Code)

**Prompt del integrante completo:**
> Un compañero trabajo en la primera issue, ya esta en main y ya importe los cambios a mi rama, el problema es que no me deja hacer deploy en render, me da este error:
> [se adjuntó el log del pre-deploy: `ValueError: DEVICE_API_KEY no está definida...` y `Pre-deploy has failed`]

**Respuesta de la IA (resumen):**
El código estaba bien: la variable `DEVICE_API_KEY` no existía en Render. Con `sync: false`, un Blueprint que ya existe **no crea el valor**, así que hay que agregarlo a mano en *Environment*. Dio los pasos: generar la clave en local con `secrets.token_urlsafe(32)`, cargarla en Render, redesplegar y no subirla al repositorio. Quitó `scope: project`, un campo que no existe en la especificación de Blueprints.

**Alternativas consideradas:**
- `generateValue: true` en `render.yaml`: la clave la genera Render y luego se copia al ESP32.
- Carga manual con `sync: false`. Se mantuvo la opción que ya había elegido el compañero.
- **Mover la validación de producción a `create_app`**, para que las migraciones no dependan del secreto. **No se aplicó** porque es código de la issue de otro integrante: quedó como sugerencia (prompt #13).

**Validación:**
- Se reprodujo el error en local con `ENVIRONMENT=production` y sin clave; con la clave, la migración pasó.
- 140 tests con 98.7 % de cobertura; ruff y mypy limpios.
- La especificación de Render se consultó en su documentación oficial.

**Qué se aceptó:** El diagnóstico y la limpieza de `render.yaml`, que llegó a `main` en el commit `6bdcd80`.

**Qué se denegó:** Pegar una clave generada en el chat. La IA pidió generarla en local.

**Qué se modificó:** Nada.

---

# Martin Contreras - Prompt #13

### IA utilizada: Claude Opus 5 (Claude Code)

**Prompt del integrante completo:**
> explica la sugerencia para que la agregue como  comentario

**Respuesta de la IA (resumen):**
Redactó un comentario listo para pegar. Explica que `Settings.from_env()` se ejecuta al importar `db.py` y `alembic/env.py`, y por eso las migraciones fallan sin una clave que no usan. Propone una función `ensure_runtime_ready(settings)` llamada desde `create_app()`. El requisito se mantiene, porque uvicorn no arranca sin la clave, pero las migraciones dejan de depender del secreto. Incluyó criterios de aceptación y la prioridad Should.

**Alternativas consideradas:** Dejarlo como está, validar en `create_app()`, o validar en la dependencia de cada request. Se descartó la última porque la app arrancaría abierta y fallaría recién en la primera petición.

**Validación:** El razonamiento se apoya en las importaciones reales del código (`src/db.py`, `alembic/env.py`) y en el error observado en Render.

**Qué se aceptó:** Publicar el texto como comentario para el compañero.

**Qué se denegó:** Nada.

**Qué se modificó:** Nada.

---

# Martin Contreras - Prompt #14

### IA utilizada: Claude Opus 5 (Claude Code)

**Prompt del integrante completo:**
> tambien al parecer realizaron la autenticacion de dispositivos por api key para la ingesta de lecturas, revisa su funcionamiento

**Respuesta de la IA (resumen):**
Probó la autenticación con TestClient y contra un uvicorn real en modo producción.

**Funciona bien:** sin clave, con encabezado vacío o con clave incorrecta responde 401; con la clave correcta, 201; los `GET` son públicos; Swagger muestra el botón *Authorize*; y la comparación usa `compare_digest`.

**Problemas encontrados:**
1. **Bug:** una clave con caracteres no ASCII (por ejemplo `ñ`) provoca **500**, porque `compare_digest` lanza `TypeError`. Se confirmó en el log del servidor.
2. **Estado global:** `create_app` guarda la configuración en una variable de módulo. Si se crea la app A con `clave-A` y luego la app B con `clave-B`, **la app A acepta `clave-B`**. En producción no afecta, pero rompe el diseño y los tests pasan de casualidad.
3. Los ejemplos del ESP32 **no enviaban** el encabezado `X-API-Key`.
4. Ramas sin tests: el error de producción en `config.py` y la respuesta "clave no configurada" en `dependencies.py`.
5. Menor: sin clave en el servidor, un 503 sería más preciso que un 401.

**Alternativas consideradas (arreglos propuestos):** comparar en bytes; guardar la configuración en `app.state.settings`; agregar el encabezado a los ejemplos; y agregar tests de esas ramas.

**Validación:** Pruebas ejecutadas con un script temporal y con peticiones HTTP crudas al servidor. La prueba generó por accidente un archivo vacío `db` en el repositorio; la IA lo revisó (0 bytes, creado en ese momento) y lo borró.

**Qué se aceptó:** El diagnóstico, que queda como tareas para el equipo con prioridades Must, Should y Could.

**Qué se denegó:** Que la IA corrigiera directamente el código del compañero. Lo decide el autor en su PR.

**Qué se modificó:** Nada.

---

# Martin Contreras - Prompt #15

### IA utilizada: Claude Opus 5 (Claude Code)

**Prompt del integrante completo:**
> que consideracion tengo que tener en el esp32 por que me dice que rechaza las solicitudes por el key

**Respuesta de la IA (resumen):**
Primero comprobó que no hubiera firmware en el repositorio y que los ejemplos de la documentación no enviaran la clave y usaran `http://`. Luego dio una guía:

1. Distinguir el tipo de rechazo por el cuerpo de la respuesta: "Not authenticated", "API key inválida" o "no configurada".
2. Llamar a `addHeader` **después** de `http.begin()`, porque `begin()` reinicia los encabezados.
3. Usar `https://` con `WiFiClientSecure`: la redirección de HTTP a HTTPS puede perder los encabezados de un POST. `setInsecure()` solo para la demo.
4. Usar la clave exacta: sin espacios ni saltos de línea y solo con caracteres ASCII.
5. Probar primero con `curl` desde la PC.
6. Guardar la clave en `secrets.h` y no ponerla en un proyecto público de Wokwi.

**Alternativas consideradas:** `setInsecure()` para la demo contra `setCACert()` con el certificado raíz. Se recomendó documentar la primera como limitación conocida.

**Validación:** **No se probó en hardware**; la IA lo declaró. La guía se basa en el comportamiento de la API verificado en el prompt #14.

**Qué se aceptó:** La guía para depurar el ESP32.

**Qué se denegó:** Nada.

**Qué se modificó:** Nada.

---

# Martin Contreras - Prompt #16

### IA utilizada: Claude Opus 5 (Claude Code)

**Prompt del integrante completo:**
> en la api integramos un html con sus imagenes y demas, perome gustaria modificarlo para que sea mas como un dashboard como en la issue que pusimos, tengo un ejemplo del diseño y formato que podria tener, solo adaptalo a la api actual:
> [se adjuntó una plantilla HTML "SolarPulse" de unas 900 líneas con Tailwind, Chart.js y datos simulados]

**Respuesta de la IA (resumen):**
Adaptó la plantilla a `src/public/` (`index.html`, `main.js`, `style.css`) usando **solo datos que la API mide**. Tiene 6 pestañas: vista general, celdas, análisis, anomalías, estado del servicio, y proyecto y equipo. Esta última conserva la landing del compañero. Agregó selector de período, pausa, actualización automática y exportación a CSV.

**Alternativas consideradas y decisiones:**
- **Se quitaron** corriente, temperatura, potencia en kW, irradiancia, strings e inversor: la API no los mide y mostrarlos sería inventar datos en la demo.
- **Se quitó** el formulario de API key y token de la plantilla: expondría la clave de los dispositivos en el navegador. El dashboard solo hace `GET` públicos.
- Tailwind desde CDN contra CSS compilado con Tailwind CLI. Se usó el CDN con **versión fija**, y la IA advirtió que muestra un aviso de "no usar en producción".
- Los nombres de celda vienen de la API y se insertan con `innerHTML`, así que se agregó `escapeHtml` para evitar XSS.

**Validación:**
- **TDD:** `tests/integration/test_dashboard_contract.py`, visto en rojo antes de implementar. Comprueba que `main.js` solo llame `GET` que existen en el OpenAPI, que no envíe escrituras ni la API key, que escape el texto y que los CDN tengan versión fija.
- Se verificó que las 3 URLs de CDN respondieran 200.
- 146 tests con 98.7 % de cobertura; ruff, `ruff format` y mypy limpios.
- **Prueba en navegador** con datos cargados por la API: todas las pestañas, el detalle de celda, el filtro de anomalías, el cambio de período, la vista móvil sin scroll horizontal y el estado sin conexión.
- **XSS:** se registró una celda con ubicación `<img src=x onerror=alert(1)>` y se mostró como texto.
- El navegador reveló problemas que los tests no detectaban (nombres cortados, rutas desbordadas, el mensaje "Failed to fetch") y se corrigieron.

**Qué se aceptó:** El dashboard, en `main` con el commit *"feat: improve photovoltaic dashboard"* (`6bdcd80`).

**Qué se denegó:** Los datos simulados y el campo de token de la plantilla original.

**Qué se modificó:** La plantilla del integrante se reescribió a partir de los datos reales. El diseño visual (paleta, tarjetas, barra lateral) se mantuvo.

**Pendientes que dejó explícitos:** compilar Tailwind para quitar el aviso de la consola, y los 404 de `/summary` en celdas sin lecturas.

---
