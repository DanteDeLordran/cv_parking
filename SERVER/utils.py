import logging
from cryptography.fernet import Fernet
import queue
from datetime import datetime, timedelta
import time
import matplotlib.pyplot as plt

KEY = b'K_nMxEqBhZtE4Jyo-KkIrs24DSV5wGuuu1F7-s0urbY='
cipher_suite = Fernet(KEY)

request_queue = queue.Queue()

# Agregar solicitud a la cola
def add_to_queue(request_data):
    request_queue.put(request_data)

# Procesar cola de solicitudes
async def process_queue():
    while True:
        if not request_queue.empty():
            request_data = request_queue.get()
            await handle_request(request_data)
        await asyncio.sleep(1)

# Procesar solicitud en la cola
async def handle_request(request_data):
    try:
        decrypted_data = cipher_suite.decrypt(request_data.encode('utf-8')).decode('utf-8')
        # Lógica para procesar solicitud
        print(f"Processed request: {decrypted_data}")
    except Exception as e:
        print(f"Error processing request: {e}")
        logging.error(f"Error processing request: {e}")

# Generar gráfico de estadísticas
def generate_stats_plot(stats):
    plt.figure()
    plt.plot([s['timestamp'] for s in stats], [s['value'] for s in stats])
    plt.xlabel('Timestamp')
    plt.ylabel('Value')
    plt.title('Statistics Plot')
    plt.grid(True)
    plt.savefig('static/stats.png')

# Guardar logs cada 24 horas
def save_logs():
    while True:
        now = datetime.now()
        next_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        time_to_midnight = (next_midnight - now).total_seconds()
        time.sleep(time_to_midnight)
        logging.info("Daily logs saved")
        # Código para guardar logs
