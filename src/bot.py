from ppi_client.ppi import PPI
from datetime import datetime
from dotenv import load_dotenv
from os import getenv

try: 
    from .config import configurar_logging, HUSO_HORARIO_ARG, CIERRE_MERVAL, APERTURA_MERVAL
    from .database import guardar_tasas
except ImportError:
    from config import configurar_logging, HUSO_HORARIO_ARG, CIERRE_MERVAL, APERTURA_MERVAL
    from database import guardar_tasas

#----------------------------------------
# Config basica
#----------------------------------------

load_dotenv()

public_key=getenv('PPI_PUBLIC_KEY')
private_key=getenv('PPI_SECRET_KEY')

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
    hoy = datetime.now(HUSO_HORARIO_ARG).weekday()

    if hoy >= 5:
        return True
    else: 
        return False

#----------------------------------------
# GETTERS y SETTERS
#----------------------------------------

def get_tasas_caucion() -> dict:
    """Obtener tasas y volumen de cauciones (24h, 48h, 72h, 168h)"""

    tasas = {}

    if ppi is None:
        _conectar_ppi()

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

def mercado_abierto() -> bool:
    """Verificar si el MERVAL está abierto"""
   
    ahora = datetime.now(HUSO_HORARIO_ARG).time()

    if _es_fin_de_semana():
        return False
    elif ahora <= APERTURA_MERVAL:
        return False
    elif ahora >= CIERRE_MERVAL:
        return False
    else:
        return True
    
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

#Trabajar mensaje, no me convence el formato actual
def mostrar_tasas(tasas: dict, mercado_cerrado: bool, cambios: dict = None) -> str:
    '''Dar formato a mensaje de tasas'''
    if not tasas:
        return "❌ Error al obtener las tasas de cauciones"

    if mercado_cerrado:
        mensaje = "🔒 *MERCADO CERRADO*\n\n📊 *Últimas tasas registradas:*\n\n"
    else:
        mensaje = "📊 *TASAS DE CAUCIONES*\n\n"

    for periodo in [('1d'), ('2d'), ('3d'), ('7d')]:
        rate = tasas[periodo]
        volumen = tasas[f'volumen_{periodo}']
        mensaje += f"🕐 {periodo.upper()}: {rate}% TNA"

        if cambios and periodo in cambios and cambios[periodo]['changed']:
            cambio = cambios[periodo]

            if cambio['absolute'] > 0:
                flecha = "📈"
                signo = "+"
            else:
                flecha = "📉"
                signo = ""
            
            mensaje += f" {flecha} {signo}{cambio['absolute']:.2f}%"
        
        mensaje += f'\n💰 Volumen: {volumen}\n'
        mensaje += "\n"

    mensaje += f"🗓️  Actualizado: {tasas['timestamp']}"

    if not mercado_cerrado:
        mensaje += "\n\n📅 *Horario del mercado:* Lun-Vie 10:30 - 17:00"

    return mensaje


datos = get_tasas_caucion()
print(datos)

tasas_antes = {'1d': 80.1, 'volumen_1d': '4.993.156.072.351',
     '2d': 17.5, 'volumen_2d': '0',
     '3d': 19.0, 'volumen_3d': '0',
     '7d': 18.3, 'volumen_7d': '86.343.528.013',
     'timestamp': '2026-05-28 23:04:55'
}

tasas_ahora = {'1d': 30.1, 'volumen_1d': '4.993.156.072.351',
     '2d': 27.5, 'volumen_2d': '0',
     '3d': 29.0, 'volumen_3d': '0',
     '7d': 38.3, 'volumen_7d': '86.343.528.013',
     'timestamp': '2026-05-28 23:04:55'
}

test_cambios = calcular_cambios_en_tasas(tasas_antes, tasas_ahora)
print(test_cambios)

mensaje_tasas = mostrar_tasas(tasas_ahora, True, test_cambios)
print(mensaje_tasas)