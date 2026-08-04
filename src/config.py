from os import getenv
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
from datetime import time
import logging

load_dotenv()

# Bandera global de test/producción, seteada desde el .env
MODO_TEST = getenv('TEST', 'False').strip().lower() == 'true'

# Setear huso horario
HUSO_HORARIO_ARG = ZoneInfo("America/Buenos_Aires")

# Horario del MERVAL
APERTURA_MERVAL = time(10, 30)
CIERRE_MERVAL = time(17, 0)

# Importar datos para la conexión al server
def server_config(test:bool = False) -> dict:
    config = {
        'host': getenv('DB_HOST'),
        'port': int(getenv('DB_PORT', '5432')),
        'user': getenv('DB_USER'),
        'password': getenv('DB_PASS'),
        'dbname': getenv('DB_NAME_TEST' if test else 'DB_NAME')
    }
    return config

# Config logger
def configurar_logging():
    LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

    logging.basicConfig(
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        level=logging.INFO
    )

    # Reducir logs de librerías externas
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('telegram').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)

    return logging.getLogger('cauchoBot')
