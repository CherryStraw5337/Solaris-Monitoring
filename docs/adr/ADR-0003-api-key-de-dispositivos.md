# ADR-0004: Autenticación de dispositivos por API key en la escritura

## Estado
Aceptado. Implementado el 13 de septiembre de 2026 (commit `9d4641d`, issue [#14](https://github.com/CherryStraw5337/Solaris-Monitoring/issues/14)); este ADR se registra el 15 de septiembre para dejar por escrito una decisión que ya está en producción.

## Contexto

Hasta la Semana 2 la API aceptaba `POST /api/v1/readings` de cualquiera que conociera la URL. Con el servicio expuesto en internet eso significa que un tercero puede inyectar lecturas falsas, y una lectura falsa no es solo ruido: contamina la eficiencia calculada de una celda y puede disparar o esconder una anomalía. El valor del producto depende de que los datos vengan del hardware real.

Al mismo tiempo, el dashboard público consume `GET /api/v1/cells` y `GET /api/v1/readings` desde el navegador. Cualquier credencial que necesitara el lado de lectura quedaría escrita en el JavaScript servido, es decir, no sería una credencial.

Quien escribe no es una persona con sesión: es un ESP32 sin pantalla ni teclado, que se programa una vez y se cuelga en un techo. Eso descarta cualquier esquema que exija un flujo interactivo o renovar un token a mano.

## Decisión

* **Frontera en la operación, no en el recurso.** Los `GET` son públicos; `POST`, `PUT` y `DELETE` exigen credencial. Los datos de una instalación fotovoltaica no son secretos; lo que hay que proteger es quién puede alterarlos.
* **Encabezado `X-API-Key`**, declarado con `APIKeyHeader` de FastAPI en `src/utils/dependencies.py`. Al ser un esquema de seguridad de OpenAPI, aparece en `/docs` con el botón *Authorize* y el jurado puede probar los endpoints protegidos sin curl.
* **Una sola clave compartida** para todos los dispositivos, en la variable de entorno `DEVICE_API_KEY`. No hay registro de dispositivos ni claves por placa.
* **Comparación con `secrets.compare_digest`**, no con `==`, para que el tiempo de respuesta no filtre cuántos caracteres del prefijo son correctos.
* **En producción la clave es obligatoria y se valida al arrancar.** `Settings.from_env` lanza `ValueError` si `ENVIRONMENT=production` y no hay `DEVICE_API_KEY`. El servicio no levanta sin clave: falla el pre-deploy en Render y la versión anterior sigue en línea, en lugar de quedar abierta sin que nadie se entere.
* **Sin clave configurada, los endpoints de escritura responden 401**, nunca 200. El caso «servidor mal configurado» se trata como no autorizado, no como permitido.

## Alternativas Descartadas

* **OAuth2 con usuarios y contraseñas (`OAuth2PasswordBearer`).** Descartada. Está pensada para personas con sesión; un ESP32 tendría que guardar un usuario y una contraseña y además renovar el token, lo que agrega una máquina de estados al firmware a cambio de ninguna seguridad extra en nuestro caso de uso.
* **JWT firmados por dispositivo.** Descartada por alcance. Resolvería la identidad por placa, pero exige emitir, firmar, caducar y rotar tokens, y con dos dispositivos en el reto el costo no se paga.
* **Una clave por dispositivo, guardada en base de datos.** Pospuesta, no descartada. Es el camino natural si el producto crece: permitiría revocar una placa sin tocar a las demás y saber qué dispositivo envió cada lectura. Requiere una tabla, un alta de dispositivos y migraciones, y no cabía antes del cierre.
* **Proteger también los `GET`.** Descartada. Rompería el dashboard, que es lo que hace demostrable el producto, y obligaría a publicar la clave en el JavaScript del navegador, que es equivalente a no tener clave.
* **Lista blanca de IPs.** Descartada: el ESP32 sale por una red doméstica con IP dinámica.

## Consecuencias

* **Positivas:** la superficie de escritura queda cerrada con una dependencia de FastAPI que se agrega función por función (`_: ApiKeyDep`), sin middleware global que después haya que exceptuar. El dashboard sigue funcionando sin credenciales. La clave vive solo en variables de entorno, nunca en el repositorio.
* **La ingesta por MQTT no pasa por esta clave.** Ahí la frontera son las credenciales del broker: quien puede publicar en HiveMQ puede insertar lecturas. Son dos puertas distintas con dos llaves distintas, y ambas deben rotarse si alguna se expone.
* **Una clave compartida se revoca para todos a la vez.** Si una placa se compromete, hay que cambiar la clave y reprogramar todas las demás.
* **Sin trazabilidad por dispositivo:** una lectura guardada no dice qué placa la envió, solo a qué celda dice pertenecer.
* **Limitación conocida:** `secrets.compare_digest` sobre cadenas de texto exige caracteres ASCII. Una clave con acentos o emoji provocaría un `TypeError` y un 500 en lugar de un 401. Las claves se generan en local con caracteres ASCII, pero la comparación debería hacerse sobre bytes.
