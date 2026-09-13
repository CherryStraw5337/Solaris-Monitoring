import json
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from db import SessionLocal  # Importa tu sesión de base de datos
from utils.repositories.reading_repo import SqlAlchemyReadingRepository
from utils.services.reading_service import ReadingService

# Credenciales de tu HiveMQ Cloud
MQTT_BROKER = "77bc782066404afd905e5dba6d27d880.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "JoseB"       # El mismo usuario que creaste en HiveMQ
MQTT_PASSWORD = "13422004"   # La contraseña de ese usuario
MQTT_TOPIC = "solaris/edsia_beyond/cell_1/voltage"

# CORREGIDO: Firma compatible con CallbackAPIVersion.VERSION2
def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("Conectado exitosamente al broker MQTT desde FastAPI")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Error de conexión MQTT, código: {reason_code}")

def on_message(client, userdata, msg):
    try:
        # 1. Decodificar el JSON que manda el ESP32
        payload_str = msg.payload.decode("utf-8")
        data = json.loads(payload_str)
        
        cell_id = data.get("cell_id")
        voltage = data.get("voltage_measured")
        
        print(f"Mensaje MQTT recibido -> Celda: {cell_id}, Voltaje: {voltage}V")

        # 2. Abrir una sesión de base de datos e insertar la lectura usando tus servicios existentes
        db: Session = SessionLocal()
        try:
            # Aquí llamas a tu repositorio o servicio de lecturas ya programado
            reading_repo = SqlAlchemyReadingRepository(db)
            # Guarda el registro en la base de datos PostgreSQL de Render
            reading_repo.create_reading(cell_id=cell_id, voltage=voltage)
            db.commit()
            print("✓ Lectura guardada en la base de datos exitosamente")
        except Exception as e:
            db.rollback()
            print(f"✗ Error al guardar en BD: {e}")
        finally:
            db.close()

    except Exception as e:
        print(f"Error procesando el mensaje MQTT: {e}")

def start_mqtt_client():
    try:
        # Generar un ID único para el cliente de Python para evitar bloqueos del broker
        import random
        client_id = "FastAPI-Subscriber-" + str(random.randint(0, 0xffff))
        
        client = mqtt.Client(client_id=client_id, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
        
        # Configurar TLS obligatorio para HiveMQ Cloud
        client.tls_set() 
        
        client.on_connect = on_connect
        client.on_message = on_message

        print(f"Intentando conectar sincrónicamente a HiveMQ ({MQTT_BROKER}:{MQTT_PORT})...")
        
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
    except Exception as e:
        print(f"✗ Error crítico al iniciar el cliente MQTT: {e}")