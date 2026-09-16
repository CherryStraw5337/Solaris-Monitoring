# ADR-0005: Despliegue continuo en Render con migraciones antes del tráfico

## Estado
Aceptado. Implementado entre el 12 y el 13 de septiembre de 2026 (`render.yaml` en el commit `22fcf9a`, pre-deploy en `ad981a9`); este ADR se registra el 15 de septiembre para dejar por escrito una decisión que ya está en producción.

## Contexto

Las bases exigen un servicio vivo con `/health` y `/docs` accesibles durante todo el reto y toda la semana de evaluación, y **evidencia de que un commit actualiza producción**. No basta con que la aplicación esté desplegada: hay que poder demostrar que lo desplegado es lo que está en `main`.

El proyecto ya se empaqueta en una imagen Docker que el CI construye, y el esquema de base de datos lo gestiona Alembic, no la aplicación: `create_app` no llama a `create_all`. Eso significa que cada despliegue que cambie el modelo necesita ejecutar una migración, y que el orden entre migrar y recibir tráfico importa.

Un detalle del proyecto condiciona el proceso: el suscriptor MQTT vive dentro del proceso web y se inicia en el `lifespan` de FastAPI (ver [ADR-0002](ADR-0002-mqtt-broker.md)).

## Decisión

* **Render como plataforma**, con la aplicación descrita en `render.yaml` (Blueprint) en lugar de configurarse a mano en el panel. La configuración del despliegue se revisa en pull requests como cualquier otro archivo.
* **Runtime Docker**, la misma imagen que construye el CI. El entorno de producción no se parece al de desarrollo: es el mismo.
* **Despliegue automático desde `main` en cada commit** (`autoDeployTrigger: commit`). Se eligió sobre `checksPass` porque los commits de versión que publica semantic-release usan el `GITHUB_TOKEN`, que por diseño no dispara flujos de trabajo: esos commits nunca tendrían checks y el servicio dejaría de desplegarse para siempre. La calidad ya se bloquea en el CI del pull request, antes de llegar a `main`.
* **Las migraciones corren en el pre-deploy**, no en el arranque de la aplicación: `preDeployCommand: alembic upgrade head`. Render lo ejecuta en una instancia aparte antes de mover el tráfico. Si la migración falla, el despliegue se cancela y **la versión anterior sigue atendiendo**.
* **Un solo proceso**, sin `--workers`. Cada worker de uvicorn abriría su propio suscriptor MQTT y cada lectura publicada se guardaría tantas veces como workers hubiera.
* **`healthCheckPath: /health`**, para que Render no mande tráfico a una instancia que todavía no responde.
* **`/health` expone el commit y la rama desplegados**, leyendo `RENDER_GIT_COMMIT` y `RENDER_GIT_BRANCH`. Esta es la evidencia que piden las bases: cualquiera compara esa respuesta con el último merge en GitHub y comprueba el despliegue continuo sin creerle a nadie.
* **Los secretos se cargan a mano** (`sync: false` para `DEVICE_API_KEY`, `MQTT_HOST`, `MQTT_USERNAME` y `MQTT_PASSWORD`). El Blueprint declara que existen; sus valores nunca entran al repositorio.
* **La URL de la base de datos se normaliza al leerla.** Render entrega `postgres://`, con lo que SQLAlchemy asume `psycopg2`, que no está instalado; `normalize_database_url` la reescribe a `postgresql+psycopg://` (psycopg 3).

## Alternativas Descartadas

* **GitHub Pages.** Descartada por imposible, no por conveniencia: solo sirve archivos estáticos. Podría alojar el dashboard, pero no un proceso Python, ni PostgreSQL, ni `/health`, ni el suscriptor MQTT. El dashboard sin API detrás no cumple nada de lo que piden las bases.
* **Migrar al arrancar la aplicación** (en el `lifespan` o con `create_all`). Descartada. Con más de una instancia, dos procesos correrían `alembic upgrade head` a la vez sobre la misma base; y una migración fallida dejaría el servicio caído en lugar de cancelar el despliegue. El `CMD` del Dockerfile sí migra antes de arrancar, pero eso es para `docker compose` en local, donde hay un solo contenedor; en Render, `dockerCommand` lo sustituye.
* **`autoDeployTrigger: checksPass`.** Descartada por el motivo explicado arriba: los commits de semantic-release nunca tendrían checks y congelarían el despliegue.
* **Desplegar desde GitHub Actions con un deploy hook.** Descartada por no duplicar la lógica de despliegue en dos sitios. Render ya observa `main`; agregar un paso en el flujo de trabajo daría dos fuentes de verdad sobre qué está desplegado.
* **Plan gratuito de Render para el servicio web.** Descartado. Las instancias gratuitas se suspenden por inactividad y tardan en despertar; las bases exigen el servicio vivo toda la semana de evaluación y un jurado que abra la URL no debería esperar medio minuto. La base de datos sí usa plan gratuito.
* **Un VPS propio con Docker Compose.** Descartada por costo de operación: habría que encargarse de TLS, reinicios, respaldos y actualizaciones del sistema durante las tres semanas del reto.

## Consecuencias

* **Positivas:** el despliegue continuo es verificable desde fuera, en una sola petición a `/health`. Una migración rota no tira producción. La configuración del despliegue vive en el repositorio y se revisa como código.
* **`main` es producción.** Cualquier merge llega a los usuarios en minutos, así que la revisión de las pull requests es la única compuerta real antes del público.
* **Techo de escalado:** mientras el suscriptor MQTT viva dentro del proceso web, el servicio no puede correr con varios workers ni con varias instancias sin duplicar lecturas. Escalar exige antes sacar el suscriptor a un proceso propio.
* **Dependencia de un proveedor:** `render.yaml`, el pre-deploy y las variables `RENDER_GIT_*` son específicos de Render. Mudarse a otra plataforma exige rehacer esa parte, aunque la imagen Docker sí es portable.
* **`sync: false` no crea la variable en un Blueprint ya existente:** al sincronizar, Render la ignora y hay que agregarla a mano en el entorno del servicio. Olvidarlo es exactamente lo que hizo fallar un pre-deploy el 14 de septiembre, cuando `DEVICE_API_KEY` no estaba definida.
