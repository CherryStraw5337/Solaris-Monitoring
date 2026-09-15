# ADR-0002: Ingesta de lecturas por MQTT como canal especializado para IoT

## Estado
Aceptado (Visto bueno de la coordinación - Cambio de alcance posterior a la Compuerta 1).

## Contexto
Para especializar nuestro producto IoT y aportar al sello de innovación, requerimos que los dispositivos con conexión intermitente y batería limitada publiquen sus lecturas mediante un protocolo ligero. Abrir una conexión HTTP completa en cada medición genera un consumo energético innecesario.
El reto de infraestructura radica en que nuestro actual proveedor (Render) no soporta el alojamiento de un broker MQTT propio, dado que sus Web Services únicamente exponen un puerto HTTP y no permiten la apertura de puertos TCP puros.

Se desarrollaron dos implementaciones en paralelo: un listener integrado en `main` (conectado al firmware real) y un adaptador en la rama `lyla` (PR con este ADR). Esta decisión consolida ambas en una sola.

## Decisión
Se ha decidido implementar la ingesta de datos mediante el siguiente enfoque:
* **Broker Gestionado:** Utilizaremos HiveMQ Cloud (Serverless) con seguridad TLS a través del puerto 8883, aprovechando que ya comprobamos su compatibilidad con las credenciales y la estructura JSON de nuestro firmware de ESP32.
* **Patrón Arquitectónico (SOLID):** El cliente MQTT se implementa como un adaptador de entrada (`MqttListener` en `src/utils/mqtt_listener.py`), al mismo nivel que el router HTTP.
* **Reutilización de Lógica:** El adaptador valida el payload con el mismo esquema (`ReadingCreate`) y guarda la lectura con el mismo servicio (`ReadingService.create`). La eficiencia y la anomalía las calcula siempre el servidor.
* **Configuración:** Solo por variables de entorno (`MQTT_HOST`, `MQTT_PORT`, `MQTT_USERNAME`, `MQTT_PASSWORD`, `MQTT_TOPIC`). Sin `MQTT_HOST` la API arranca sin MQTT; con host pero sin credenciales, falla al iniciar.
* **Ciclo de vida:** El cliente se inicia en el `lifespan` de FastAPI con `connect_async` + `loop_start` (no bloquea el arranque; paho reintenta la conexión) y se desconecta al apagar. La suscripción usa QoS 1.
* **Contrato del mensaje:** un topic compartido por todas las celdas, `solaris/readings`, con `cell_id` y `voltage_measured` en el JSON. Cada placa define su `CELL_ID` en `secrets.h`; `render.yaml` y `src/firmware/esp32/MQTT.ino` usan el mismo topic y un test lo verifica.
* **Observabilidad:** `GET /health` expone `mqtt_status` (`disabled`, `connecting`, `connected`, `disconnected`).

## Alternativas Descartadas
* **Broker autoalojado en Render:** Se descartó completamente porque la plataforma no permite exponer los puertos TCP nativos (1883/8883) requeridos para establecer la conexión con los sensores.
* **Guardar la lectura directamente desde el callback MQTT:** Descartado. Duplicaba reglas (eficiencia contra 3.3 V fijos, sin anomalías ni validación de celda) y producía datos distintos a los de HTTP.
* **Topic por celda `solaris/cells/{cell_id}/readings` (propuesto en el PR):** Pospuesto, no descartado. El soporte multicelda ya se obtiene con el topic compartido; el topic por celda agregaría permisos por dispositivo en HiveMQ (una placa solo podría publicar en su celda), a cambio de cambiar la API, el firmware y Render antes del cierre del reto.
* **Configuración MQTT dentro de `Settings`:** Descartado para no duplicar `MqttConfig`, que además exige credenciales cuando hay host.

## Consecuencias
* **Positivas:** Especialización del canal para hardware IoT, ahorro de batería en el ESP32, y protección absoluta del dominio (no se duplica ninguna regla de negocio). Un fallo del broker no impide que la API atienda HTTP.
* **Riesgos:** Añadimos una dependencia de infraestructura a un servicio de terceros (HiveMQ Cloud). Las credenciales del broker deben rotarse si se exponen.
* **Limitaciones actuales:** Con el topic compartido, cualquier dispositivo con credenciales del broker puede enviar lecturas de cualquier `cell_id`. El suscriptor corre dentro del proceso web: con varios workers de uvicorn cada uno se suscribiría y las lecturas se guardarían repetidas, por lo que el servicio debe mantenerse con un solo proceso.
