from ppi_client.ppi import PPI
from datetime import datetime
from dotenv import load_dotenv
from os import getenv

try:
    from .config import configurar_logging, HUSO_HORARIO_ARG, CIERRE_MERVAL, APERTURA_MERVAL
except ImportError:
    from config import configurar_logging, HUSO_HORARIO_ARG, CIERRE_MERVAL, APERTURA_MERVAL

#----------------------------------------
# Config basica
#----------------------------------------

load_dotenv()

# PPI siempre apunta a la API productiva, independientemente de MODO_TEST
public_key = getenv('PPI_PUBLIC_KEY')
private_key = getenv('PPI_SECRET_KEY')

logger = configurar_logging()

ppi = None

#----------------------------------------
# Métodos PRIVADOS
#----------------------------------------

def _conectar_ppi():
    global ppi
    ppi = PPI(sandbox=False)
    ppi.account.login_api(public_key, private_key)

    logger.info("Conectado a PPI exitosamente")

def _es_fin_de_semana() -> bool:
    return datetime.now(HUSO_HORARIO_ARG).weekday() >= 5

#----------------------------------------
# GETTERS y SETTERS
#----------------------------------------

def get_tasas_caucion() -> dict:
    """Obtener tasas y volumen de cauciones (24h, 48h, 72h, 168h) desde la API de PPI"""

    tasas = {}

    if ppi is None:
        _conectar_ppi()

    try:
        tasa24h = ppi.marketdata.current("PESOS1", "CAUCIONES", "INMEDIATA")
        tasas['1d'] = float(tasa24h.get('price', 0))
        tasas['volumen_1d'] = int(tasa24h.get('volume', 0))

        tasa48h = ppi.marketdata.current("PESOS2", "CAUCIONES", "INMEDIATA")
        tasas['2d'] = float(tasa48h.get('price', 0))
        tasas['volumen_2d'] = int(tasa48h.get('volume', 0))

        tasa72h = ppi.marketdata.current("PESOS3", "CAUCIONES", "INMEDIATA")
        tasas['3d'] = float(tasa72h.get('price', 0))
        tasas['volumen_3d'] = int(tasa72h.get('volume', 0))

        tasa168h = ppi.marketdata.current("PESOS7", "CAUCIONES", "INMEDIATA")
        tasas['7d'] = float(tasa168h.get('price', 0))
        tasas['volumen_7d'] = int(tasa168h.get('volume', 0))

        tasas['timestamp'] = datetime.now(HUSO_HORARIO_ARG).strftime("%Y-%m-%d %H:%M:%S")

        return tasas
    
    except Exception as e:
        logger.error(f"Error obteniendo tasas: {e}")
        return None
    
#----------------------------------------
# Métodos PUBLICOS
#----------------------------------------

def mercado_abierto() -> bool:
    """Verificar si el MERVAL está abierto"""
    ahora = datetime.now(HUSO_HORARIO_ARG).time()
    return not _es_fin_de_semana() and APERTURA_MERVAL < ahora < CIERRE_MERVAL
    
# No me gusta como quedo, hay que revisar
def calcular_cambios_en_tasas(tasas_anteriores: dict, tasas_nuevas:dict) -> dict:
    """Calcular cambios entre tasas antiguas y nuevas"""
    
    if not tasas_anteriores or not tasas_nuevas:
        return None

    cambios = {}

    for periodo in ['1d', '2d', '3d', '7d']:
        valor_anterior = tasas_anteriores.get(periodo, 0)
        valor_nuevo = tasas_nuevas.get(periodo, 0)
        
        if valor_anterior == 0:
            cambios[periodo] = {
                'absolute': 0,
                'percentage': 0,
                'changed': False
            }
        else:
            variacion_absoluta = valor_nuevo - valor_anterior
            variacion_porcentual = (variacion_absoluta / valor_anterior) * 100

            cambios[periodo] = {
                'old': valor_anterior,
                'new': valor_nuevo,
                'absolute': variacion_absoluta,
                'percentage': variacion_porcentual,
                'changed': abs(variacion_absoluta) > 0.001  # Tolerancia para floats
            }

    return cambios