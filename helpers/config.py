from dotenv import load_dotenv as cargarEnv
from zoneinfo import ZoneInfo
from datetime import time

# Setear huso horario
HUSO_HORARIO_ARG = ZoneInfo("America/Buenos_Aires")

# Horario del MERVAL
APERTURA_MERVAL = time(10, 30)
CIERRE_MERVAL = time(17, 0)

cargarEnv()
