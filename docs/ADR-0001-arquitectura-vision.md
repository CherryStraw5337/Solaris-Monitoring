## Arquitectura del Sistema de Detección de Maduración de Café



**1. Capa Edge (Hardware e Ingesta de Datos)**



* **Dispositivo:** Raspberry Pi (versión 4 o 5) con un módulo de cámara.

* **Ejecución Local:** Un script en Python que utiliza OpenCV para capturar imágenes del cultivo en intervalos definidos o mediante un disparador manual.

* **Transmisión:** El script empaqueta la imagen capturada y la envía mediante una petición HTTP POST al backend. La solicitud se autentica mediante un token configurado estrictamente como variable de entorno, asegurando el cumplimiento de la regla de cero secretos en el historial.







**2. Capa Backend (Procesamiento y API)**



* **Framework:** FastAPI estructurado bajo principios de Clean Architecture.

* **Procesamiento de IA (Sello de Innovación):** Integración de la librería Ultralytics para ejecutar el modelo de visión por computadora (como YOLOv8 o YOLO26) directamente en el servidor al recibir la imagen. El modelo segmenta los frutos de café y los clasifica por estado de maduración (verde, pintón, maduro).





* **Endpoints Principales:**

* `POST /api/v1/inferences`: Recibe la imagen de la Raspberry Pi, ejecuta la inferencia con YOLO, guarda la imagen procesada y registra los conteos en la base de datos.

* `GET /api/v1/stats`: Devuelve el historial y las estadísticas de maduración para un cliente web.

* `GET /health` y `GET /docs`: Endpoints expuestos y funcionales durante toda la competencia.











**3. Capa de Persistencia (Base de Datos)**



* **Motor:** PostgreSQL.





* **ORM y Migraciones:** SQLAlchemy 2.x para el modelado transaccional y Pydantic para la validación de esquemas de entrada/salida. Alembic gestionará de forma automatizada las migraciones del esquema.





* **Modelo de Datos Propuesto (`CaptureRecord`):**

* `id` (UUID)

* `timestamp` (DateTime)

* `device_id` (String, identifica la Raspberry Pi)

* `image_url` (String)

* `ripe_count` (Integer)

* `unripe_count` (Integer)







**4. Infraestructura y Despliegue (DevOps)**



* **Contenedores:** Un `Dockerfile` optimizado (imagen slim, aprovechando caché de capas) para la API, que incluya las dependencias de Ultralytics y OpenCV, junto con un `docker-compose.yml` que levante la API y PostgreSQL con un solo comando.





* **Integración Continua (CI):** Un pipeline en GitHub Actions que ejecute formateo con Ruff, análisis estático con Mypy y pruebas unitarias con Pytest. Es vital configurar el parámetro `fail-under=80` para que el pipeline bloquee el despliegue si la cobertura es insuficiente.





* **Despliegue Continuo (CD):** Despliegue automático a un servicio en la nube tras aprobar una Pull Request (revisada por tus compañeros) en GitHub.







**5. Elementos Estratégicos para la Evaluación**



* **Registro de Decisiones (ADR):** Crear el documento ADR-0001 explicando por qué la inferencia de YOLO se procesa en el backend en lugar de la Raspberry Pi (por ejemplo, para centralizar las actualizaciones del modelo de IA o administrar mejor los recursos del hardware de borde).





* **Bitácora AI_LOG:** Registrar cuidadosamente los prompts utilizados para generar configuraciones de Docker o plantillas de GitHub Actions, detallando qué sugirió la IA, qué se validó y qué se rechazó.

cmo hago estas modificaciones en mi rama de github para que mis oreos compañeros la vean 

