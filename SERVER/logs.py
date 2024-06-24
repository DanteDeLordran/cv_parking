import logging
from datetime import datetime, timedelta
import time

# Guardar logs cada 24 horas
def save_logs():
    while True:
        now = datetime.now()
        next_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        time_to_midnight = (next_midnight - now).total_seconds()
        time.sleep(time_to_midnight)
        logging.info("Daily logs saved")
        # Código para guardar logs
