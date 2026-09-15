# ADR-0002: Ingesta de lecturas por MQTT como canal especializado para IoT

## Estado
Aceptado (Visto bueno de la coordinación - Cambio de alcance posterior a la Compuerta 1).

## Contexto
Para especializar nuestro producto IoT y aportar al sello de innovación, requerimos que los dispositivos con conexión intermitente y batería limitada publiquen sus lecturas mediante un protocolo ligero. Abrir una conexión HTTP completa en cada medición genera un consumo energético innecesario. 
El reto de infraestructura radica en que nuestro actual proveedor (Render) no soporta el alojamiento de un broker MQTT propio, dado que sus Web Services únicamente exponen un puerto HTTP y no permiten la apertura de puertos TCP puros.

## Decisión
Se ha decidido implementar la ingesta de datos mediante el siguiente enfoque:
* **Broker Gestionado:** Utilizaremos HiveMQ Cloud (Serverless) con seguridad TLS a través del puerto 8883, aprovechando que ya comprobamos su compatibilidad con las credenciales y la estructura JSON de nuestro firmware de ESP32[cite: 1].
* **Patrón Arquitectónico (SOLID):** El cliente MQTT se implementará estrictamente como un nuevo adaptador de entrada.
* **Reutilización de Lógica:** Este adaptador validará el payload utilizando los mismos esquemas actuales (`ReadingCreate`) e inyectará los datos mediante el mismo servicio subyacente (`ReadingService.create`).

## Alternativas Descartadas
* **Broker autoalojado en Render:** Se descartó completamente porque la plataforma no permite exponer los puertos TCP nativos (1883/8883) requeridos para establecer la conexión con los sensores.

## Consecuencias
* **Positivas:** Especialización del canal para hardware IoT, ahorro de batería en el ESP32, y protección absoluta del dominio (no se duplicará ninguna regla de negocio).
* **Riesgos:** Añadimos una dependencia de infraestructura a un servicio de terceros (HiveMQ Cloud).