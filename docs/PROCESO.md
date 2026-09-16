# Proceso de trabajo

Cómo organizamos las tres semanas del Reto Final EDSIA 2026, qué entró en cada una y qué aprendimos. Equipo: Martin Contreras, Lyla Estrada, José Bello.

## Cómo trabajamos

- **Una rama por integrante** (`martin`, `lyla`, `feature-yo-merito`) y `main` siempre desplegable. Nada llega a `main` sin pull request.
- **Issues con plantilla propia** (`.github/ISSUE_TEMPLATE/`) y prioridad **MoSCoW** en cada una, para discutir qué se queda fuera antes de escribir código.
- **CI como compuerta**: ruff, formato, mypy estricto, pruebas con corte de cobertura en 90 % y migraciones aplicadas desde cero. Un pull request en rojo no se fusiona.
- **Versionado automático** con semantic-release a partir de los mensajes de commit: ocho versiones publicadas, de la v1.0.0 a la v1.6.0.
- **Decisiones importantes en ADRs** (`docs/adr/`) y uso de IA en bitácoras por integrante (`docs/ai_logs/`), con qué se pidió, qué se aceptó y qué se rechazó.

## Las tres semanas

| Semana | Qué se entregó | Evidencia |
| --- | --- | --- |
| **1 · Descubrir y diseñar**<br>26 ago — 1 sep | Repositorio nuevo creado el día del kickoff, estructura del proyecto, CI en GitHub Actions, plantillas de issue, versionado semántico, licencia y el [ADR-0001](adr/0001-stack-tecnologico-base.md) con el stack. Definición del problema y del MVP en la issue [#3](https://github.com/CherryStraw5337/Solaris-Monitoring/issues/3). | 17 commits, PRs [#1](https://github.com/CherryStraw5337/Solaris-Monitoring/pull/1) a [#4](https://github.com/CherryStraw5337/Solaris-Monitoring/pull/4) |
| **2 · Construir**<br>2 — 8 sep | Semana floja: solo dos commits llegaron al repositorio. El trabajo de esos días fue de exploración local y no quedó registrado. | 2 commits |
| **3 · Terminar y pulir**<br>9 — 15 sep | La API completa en producción, el dashboard, la autenticación por API key, la ingesta MQTT con hardware real, el paquete de documentación y la vista móvil. | 137 commits, PRs [#6](https://github.com/CherryStraw5337/Solaris-Monitoring/pull/6) a [#31](https://github.com/CherryStraw5337/Solaris-Monitoring/pull/31), v1.0.0 a v1.6.0 |

El backlog se ordenó por MoSCoW en cinco issues de desarrollo ([#12](https://github.com/CherryStraw5337/Solaris-Monitoring/issues/12) a [#16](https://github.com/CherryStraw5337/Solaris-Monitoring/issues/16)): quitar credenciales del compose y badge de CI (Must), lecturas reales del ESP32 (Must), API key de dispositivos (Should), ingesta MQTT (Could) y dashboard con datos reales (Should). Todas cerradas antes del 15 de septiembre.

## Retrospectiva

### Qué funcionó

- **Las compuertas automáticas ahorraron discusiones.** Con ruff, mypy y el corte de cobertura en el pipeline, la revisión humana de las pull requests se ocupó del diseño en lugar del estilo.
- **Separar el dominio de los canales de entrada se pagó solo.** Cuando llegó MQTT, la regla de eficiencia y la detección de anomalías no se tocaron: el suscriptor reutiliza el mismo servicio que el endpoint HTTP. Sin esa separación habríamos terminado con dos versiones de la misma regla, que fue justamente el primer intento y se descartó.
- **Migraciones antes de mover el tráfico.** Ninguna migración fallida tiró el servicio: el despliegue se cancela y la versión anterior sigue en línea.
- **Revisar el código generado por IA antes de aceptarlo.** Once errores de la IA quedaron registrados en las bitácoras con cómo se detectó cada uno, incluidos varios que llegaban a romper producción.

### Qué no funcionó

- **La Semana 2 quedó vacía en el repositorio.** Entre el 4 y el 9 de septiembre no hubo commits, y 110 de los 161 commits del proyecto se concentran en tres días (12, 13 y 14 de septiembre). Todo el riesgo se acumuló al final.
- **Dos personas implementaron la ingesta MQTT en paralelo sin saberlo**, y hubo que consolidar dos soluciones distintas contra reloj. Faltó decir en voz alta quién tomaba cada issue.
- **Se filtraron credenciales reales en el repositorio público** al pegar prompts crudos en una bitácora de IA. Un escáner externo las encontró en menos de tres horas.
- **La mitad de las pull requests se fusionó sin revisión**, incluidas varias de los últimos días, que son las que tocaban producción.
- **Contribución despareja:** 86 commits de un integrante frente a 34 y 30 de los otros dos.

### Qué haríamos distinto

1. **Asignar cada issue a una persona antes de empezar a escribir código**, y no solo priorizarla. Habría evitado el trabajo duplicado de MQTT.
2. **Tratar la compuerta semanal como fecha de entrega real**, con algo desplegado cada semana en lugar de un empujón final.
3. **Poner el escaneo de secretos en el pipeline**, no confiar en la revisión humana para detectarlos. La regla nueva es que las bitácoras de IA se editan antes de subirse y la configuración se cita por el nombre de la variable, nunca por su valor.
4. **Exigir una revisión aprobatoria en `main`** por configuración del repositorio, y no por acuerdo verbal.

## Backlog vivo

Lo que queda fuera del cierre del reto, en orden de importancia:

1. Rotar las credenciales expuestas y habilitar el escaneo de secretos del repositorio.
2. Sacar el suscriptor MQTT del proceso web, que hoy impide correr el servicio con más de una instancia sin duplicar lecturas.
3. Claves por dispositivo en lugar de una clave compartida, para revocar una placa sin reprogramar las demás (ver [ADR-0003](adr/ADR-0003-api-key-de-dispositivos.md)).
4. Un tópico por celda con permisos en el broker (ver [ADR-0002](adr/ADR-0002-mqtt-broker.md)).
5. Alertas al responsable de mantenimiento cuando una celda cruza su umbral.
6. Compilar Tailwind en lugar de servirlo desde el CDN, y enviar encabezados de caché en el dashboard para que un despliegue nuevo no quede escondido tras la copia del navegador.
