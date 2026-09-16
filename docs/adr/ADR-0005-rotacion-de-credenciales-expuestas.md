# ADR-0005: Rotación de las credenciales expuestas en el historial público

## Estado
Aceptado y ejecutado el 15 de septiembre de 2026.

## Contexto

El 13 de septiembre, al documentar la integración MQTT, se pegaron en una bitácora de IA prompts completos que incluían el sketch del ESP32 y la salida de la terminal. Esos textos llevaban dentro credenciales reales: el SSID y la contraseña de una red WiFi, la contraseña del broker MQTT y el nombre del clúster de HiveMQ Cloud. El repositorio es público.

Cronología:

| Momento | Qué ocurrió |
| --- | --- |
| 13 sep, 15:22 | El commit `a6d6633` publica las credenciales dentro de `docs/ai_logs/AI_LOG_JOSE.md`. |
| 13 sep, 18:01 | Un escáner automático externo abre la issue [#21](https://github.com/CherryStraw5337/Solaris-Monitoring/issues/21) avisando de la credencial expuesta. Pasaron 2 h 39 min desde la publicación. |
| 14 sep, 21:19 | El commit `a20779b` restaura la bitácora desde el historial para recuperar contenido perdido y **vuelve a introducir** las credenciales en el árbol de trabajo. |
| 14 sep, 21:56 | El commit `71a3904` las sustituye por marcadores. |
| 15 sep | Se rotan todas las credenciales afectadas. |

Dos hechos condicionaron la respuesta:

* **Sustituir el texto no deshace la publicación.** Los valores siguen recuperables con `git log -S` sobre cualquier clon, y el aviso del escáner prueba que hubo al menos un tercero leyendo el flujo público de commits antes de que reaccionáramos. Todo lo publicado debe tratarse como comprometido.
* **La restauración del 14 de septiembre mostró que el problema no era el descuido inicial, sino que el secreto vivía en el historial.** Una operación de recuperación rutinaria lo devolvió al árbol sin que nadie lo notara.

## Decisión

**Rotamos todas las credenciales expuestas y asumimos el historial como público.** Es la única acción que hace irrelevante lo que quedó publicado: los valores antiguos siguen ahí, pero ya no abren nada.

Lo ejecutado:

| Credencial | Acción | Cómo se comprueba |
| --- | --- | --- |
| Contraseña de la red WiFi | Cambiada en el router y actualizada en el `secrets.h` del firmware | El ESP32 vuelve a conectarse y publica lecturas |
| Usuario y contraseña del broker MQTT (HiveMQ Cloud) | Rotados en el broker y actualizados en las variables de entorno del servicio en Render | `GET /health` responde `"mqtt_status": "connected"` con las credenciales nuevas, y las lecturas siguen llegando |
| `DEVICE_API_KEY` | Regenerada y cargada en Render y en el firmware | Los endpoints de escritura aceptan la clave nueva y rechazan la anterior con 401 |

Decisiones que acompañan a la rotación:

1. **No reescribimos el historial público.** Los valores quedan en los commits antiguos; lo que deja de existir es su utilidad.
2. **Las bitácoras de IA se editan antes de subirse.** La configuración se cita por el nombre de la variable de entorno, nunca por su valor, igual que ya se hace en `.env.example` y en `secrets.example.h`. Fue la vía por la que entró el secreto y es la que se cierra.
3. **Documentamos el incidente en abierto**, en este ADR. La fuga ya es pública; ocultar la respuesta solo quitaría el único elemento que habla bien de nosotros.

## Alternativas Descartadas

* **Reescribir el historial con `git filter-repo` o `git filter-branch`.** Descartada. Cambia el hash de todos los commits del proyecto, obliga a los tres integrantes a reclonar en plena semana de cierre, rompe las referencias de las pull requests ya revisadas y deja los blobs antiguos accesibles en GitHub hasta que el proveedor los recolecte. Además no recupera el secreto: los forks y las copias de los escáneres ya lo tienen. Rotar consigue el objetivo real sin ninguno de esos costos.
* **Borrar el repositorio y volver a publicarlo limpio.** Descartada de plano: las bases evalúan el historial de trabajo real en GitHub y perderlo costaría mucho más que la fuga.
* **Borrar la bitácora afectada.** Descartada. Las bases piden la bitácora de IA de los tres integrantes; quitarla para tapar el incidente cambiaría una penalización por otra mayor.
* **No rotar, dado que los valores ya estaban sustituidos en el árbol.** Descartada. Las bases dicen que un secreto filtrado «se rota y se documenta de inmediato; manejarlo bien también se evalúa», y una contraseña de red doméstica publicada es un riesgo real fuera del proyecto.

## Consecuencias

* **Positivas:** las credenciales publicadas ya no sirven para nada. El servicio siguió en línea durante toda la rotación: se actualizaron las variables de entorno en Render y el suscriptor MQTT volvió a conectarse con las nuevas, sin interrumpir la ingesta. Queda una respuesta escrita y fechada ante un incidente real.
* **Negativas:** el historial queda permanentemente marcado y cualquiera puede leer los valores antiguos. Aceptamos ese costo a cambio de no reescribir el historial durante la semana de cierre.
* **Riesgo que permanece:** cualquier recuperación de contenido desde commits anteriores al `71a3904` puede devolver los valores al árbol. Antes de restaurar un archivo desde el historial hay que revisarlo, como enseñó el commit `a20779b`.
* **Cerrado el 15 de septiembre:** el nombre del clúster de HiveMQ aparecía en seis lugares de `docs/ai_logs/AI_LOG_JOSE.md` y quedó sustituido por marcadores en todos. El árbol de trabajo ya no contiene ninguno de los valores filtrados.
* **Pendiente:** el repositorio no tiene escaneo de secretos propio. Habilitar el escaneo y la protección de push de GitHub, o un hook de pre-commit, cerraría el hueco antes de que lo encuentre un tercero. Queda en el [backlog vivo](../PROCESO.md).
