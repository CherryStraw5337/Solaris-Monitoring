from __future__ import annotations
import json
import random
import paho.mqtt.client as mqtt
from sqlalchemy.orm import Session
from db import SessionLocal  # Importa tu sesión de base de datos
from utils.repositories.reading_repo import SqlAlchemyReadingRepository
from utils.models import Reading  # Importante para instanciar el objeto de lectura

# Credenciales de tu HiveMQ Cloud
MQTT_BROKER = "77bc782066404afd905e5dba6d27d880.s1.eu.hivemq.cloud"
MQTT_PORT = 8883
MQTT_USER = "JoseB"       # Usuario corregido
MQTT_PASSWORD = "13422004"   # Contraseña de tu usuario
MQTT_TOPIC = "solaris/edsia_beyond/cell_1/voltage"

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
        
        # Respaldo automático de eficiencia si el ESP32 no la manda todavía
        efficiency = data.get("efficiency_percentage")
        if efficiency is None:
            max_voltage = 3.3
            efficiency = round((voltage / max_voltage) * 100, 2) if voltage <= max_voltage else 100.0
        
        print(f"Mensaje MQTT recibido -> Celda: {cell_id}, Voltaje: {voltage}V, Eficiencia: {efficiency}%")

        # 2. Abrir una sesión de base de datos e insertar la lectura
        db: Session = SessionLocal()
        try:
            reading_repo = SqlAlchemyReadingRepository(db)
            
            nueva_lectura = Reading(
                cell_id=cell_id, 
                voltage_measured=voltage,
                efficiency_percentage=efficiency
            )
            reading_repo.add(nueva_lectura)
            
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

