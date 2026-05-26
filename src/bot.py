from ppi_client.ppi import PPI
from datetime import datetime
from dotenv import load_dotenv
from os import getenv
from src.config import HUSO_HORARIO_ARG

try: 
    from .config import configurar_logging
    from .database import guardar_tasas
except ImportError:
    from config import configurar_logging
    from database import guardar_tasas

#----------------------------------------
# Config basica
#----------------------------------------

load_dotenv()

public_key=getenv('PPI_PUBLIC_KEY')
private_key=getenv('PPI_SECRET_KEY')

ppi = None

def conectar_ppi():
    global ppi
    ppi = PPI(sandbox=False)
    ppi.account.login_api(public_key, private_key)

logger = configurar_logging()

#----------------------------------------
# GETTERS y SETTERS
#----------------------------------------

def get_tasas_caucion() -> dict:
    """Obtener tasas y volumen de cauciones (24h, 48h, 72h, 168h)"""

    tasas = {}

    try:

        tasa24h = ppi.marketdata.current("PESOS1", "CAUCIONES", "INMEDIATA")
        tasas['1d'] = float(tasa24h.get('price', 0))
        tasas['volumen_1d'] = f"{int(tasa24h.get('volume', 0)):,}".replace(",", ".")

        tasa48h = ppi.marketdata.current("PESOS2", "CAUCIONES", "INMEDIATA")
        tasas['2d'] = float(tasa48h.get('price', 0))
        tasas['volumen_2d'] = f"{int(tasa48h.get('volume', 0)):,}".replace(",", ".")

        tasa72h = ppi.marketdata.current("PESOS3", "CAUCIONES", "INMEDIATA")
        tasas['3d'] = float(tasa72h.get('price', 0))
        tasas['volumen_3d'] = f"{int(tasa72h.get('volume', 0)):,}".replace(",", ".")

        tasa168h = ppi.marketdata.current("PESOS7", "CAUCIONES", "INMEDIATA")
        tasas['7d'] = float(tasa168h.get('price', 0))
        tasas['volumen_7d'] = f"{int(tasa168h.get('volume', 0)):,}".replace(",", ".")

        tasas['timestamp'] = datetime.now(HUSO_HORARIO_ARG).strftime("%Y-%m-%d %H:%M:%S")

        return tasas
    
    except Exception as e:
        logger.error(f"Error obteniendo tasas: {e}")
        return None
    
#----------------------------------------
# Métodos PUBLICOS
#----------------------------------------

