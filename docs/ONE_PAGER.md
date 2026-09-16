# Solaris Monitoring — One-pager ejecutivo

**Reto Final EDSIA 2026** · Equipo: Martin Contreras, Lyla Estrada, José Bello
Producción: <https://solaris-monitoring-api.onrender.com/> · Repositorio: <https://github.com/CherryStraw5337/Solaris-Monitoring>

## El problema

Un panel fotovoltaico no se apaga cuando falla: se degrada en silencio. Sigue entregando voltaje, solo que menos del que debería, y la pérdida no se nota hasta que alguien sube con un multímetro a medir celda por celda.

Quien mantiene una instalación —el laboratorio de una facultad, el techo de una nave, un sistema aislado— no tiene forma de saber **qué celda rinde por debajo de lo suyo hoy**. Las revisiones son manuales, se hacen cada varias semanas y solo encuentran la falla cuando ya costó energía.

## La solución

Solaris Monitoring registra cada lectura de voltaje, calcula la eficiencia **contra el voltaje nominal de esa celda en particular** y marca la anomalía en el momento en que ocurre.

El dato recorre cinco pasos: el ESP32 mide en la celda, publica por MQTT sobre TLS, la API aplica sus reglas de dominio, guarda en PostgreSQL y el dashboard lo muestra. La misma lectura puede entrar por HTTP; las reglas son idénticas porque viven en un módulo de dominio que no sabe por qué canal llegó el dato.

Una lectura es anomalía si supera el voltaje máximo seguro de la celda (su nominal más 20 %) o si su eficiencia cae por debajo del umbral configurado para ella. El umbral y el nominal se definen por celda: un panel de 3 V y uno de 12 V no se juzgan con la misma vara.

## Alcance logrado

- **Producto vivo en producción** con `/health`, `/docs` y dashboard, desplegado desde `main` en cada commit. `/health` devuelve el commit y la rama que corren, así que el despliegue continuo se comprueba sin creerle a nadie.
- **Dos canales de entrada** con un solo juego de reglas: REST y MQTT sobre TLS (HiveMQ Cloud, puerto 8883). Varias celdas comparten un tópico y se distinguen por `cell_id` en el JSON.
- **Hardware real**: un ESP32 midiendo una celda física alimenta la instancia de producción.
- **Escritura autenticada** por `X-API-Key`; la lectura es pública, para que el dashboard y cualquier otro consumidor funcionen sin credenciales.
- **Dashboard** con eficiencia por celda, historial, anomalías y descarga en CSV, operable desde un teléfono sin pedir modo escritorio.
- **Calidad con compuertas reales**: 194 pruebas, 98.96 % de cobertura de rama con corte obligatorio en 90, ruff, mypy estricto y migraciones aplicadas desde cero en cada ejecución del pipeline.

## Lo que decidimos no hacer

Medimos voltaje y nada más. Corriente, irradiancia y temperatura harían el diagnóstico más rico, pero exigían más sensores de los que teníamos y tres semanas no alcanzaban para dos frentes. Preferimos un flujo completo que funciona de la celda a la gráfica antes que cinco magnitudes a medias.

## A dónde puede crecer

1. **Alertas al responsable**: hoy la anomalía se ve en el dashboard; el siguiente paso es que busque a la persona por correo o mensaje, sin que nadie tenga que mirar la pantalla.
2. **Un tópico por celda con permisos en el broker**, para que una placa solo pueda publicar lecturas de su propia celda (analizado y pospuesto en el [ADR-0002](adr/ADR-0002-mqtt-broker.md)).
3. **Predicción de degradación**: el histórico por celda ya se guarda con la granularidad necesaria para estimar cuándo una celda cruzará su umbral.
4. **Más magnitudes**: corriente e irradiancia permitirían separar una celda sucia de una celda dañada, que hoy se ven igual.

## Documentos

[README](../README.md) · [API](API.md) · [Despliegue](DEPLOYMENT.md) · [Integración ESP32](ESP32_INTEGRATION.md) · [ADRs](adr/) · [Bitácoras de IA](ai_logs/)
