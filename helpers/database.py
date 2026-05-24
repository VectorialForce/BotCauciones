from contextlib import contextmanager
from dotenv import load_dotenv
from os import getenv
import psycopg2
from config import configurar_logging

#----------------------------------------
# Config basica
#----------------------------------------

# IMPORTANTE - Bandera para apuntar a test o prod
test = True

logger = configurar_logging()
load_dotenv()

db_config = {
    'host': getenv('DB_HOST'),
    'port': int(getenv('DB_PORT', '5432')),
    'user': getenv('DB_USER'),
    'password': getenv('DB_PASS'),
    'dbname': getenv('DB_NAME')
}

db_config_test = {
    'host': getenv('DB_HOST'),
    'port': int(getenv('DB_PORT', '5432')),
    'user': getenv('DB_USER'),
    'password': getenv('DB_PASS'),
    'dbname': getenv('DB_NAME_TEST')
}

db_env = db_config_test if test else db_config

# Esto esta de modo temporal, es una responsabilidad del orquestador NO del modulo
required_vars = ['DB_HOST', 'DB_USER', 'DB_PASS', 'DB_NAME']
missing = [var for var in required_vars if not getenv(var)]
if missing:
    raise EnvironmentError(f"Variables de entorno faltantes: {', '.join(missing)}")


@contextmanager
def conectar_db():
    conn = psycopg2.connect(**db_env)
    try:
        yield conn
    finally:
        conn.close()

#----------------------------------------
# Métodos PRIVADOS
#----------------------------------------

def _verificar_conexion():
    """Verificar que la conexión es válida antes de continuar"""
    try:
        with conectar_db():
            logger.info(f"Conexión a PostgreSQL verificada: {db_env['dbname']}")
    except psycopg2.OperationalError as e:
        logger.error(f"No se pudo conectar a PostgreSQL: {e}")
    except Exception as e:
        logger.error(f"No se pudo conectar a PostgreSQL: {e}")

#----------------------------------------
# GETTERS y SETTERS
#----------------------------------------

def get_estadisticas() -> dict:
    """Obtener estadísticas de la base de datos"""

    tablas = ['subscriptions', 'rate_history', 'suggestions']
    stats = {}

    try:
        with conectar_db() as conn:
            with conn.cursor() as cur:
                for tabla in tablas:
                    cur.execute(f"SELECT COUNT(*) FROM {tabla}")
                    stats[f"{tabla}_count"] = cur.fetchone()[0]

                cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                stats["tamanio_db"] = cur.fetchone()[0]
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        return {}

    return stats
            
def get_suscripciones() -> dict | None:
    """Obtener todas las suscripciones"""
    with conectar_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT *
                FROM subscriptions
                ORDER BY created_at DESC
                """)
            
            suscripciones = {}

            for fila in cur.fetchall():
                suscripciones[fila['chat_id']] = {
                    'chat_id': fila['chat_id'],
                    'subscription_type':fila['subscription_type'],
                    'threshold_percentage' :fila['threshold_percentage']
                }

            logger.info(f"✅ Cargadas {len(suscripciones)} suscripciones desde PostgreSQL")
            return suscripciones

def get_ultimas_tasas() -> dict | None:
    """Obtener las últimas tasas registradas"""
    with conectar_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT rate_1d, rate_2d, rate_3d, rate_7d, timestamp
                FROM rate_history
                ORDER BY id DESC
                LIMIT 1
            """)
            fila = cur.fetchone()

    if fila is None:
        return None

    return {
        '1d': fila[0],
        '2d': fila[1],
        '3d': fila[2],
        '7d': fila[3],
        'timestamp': fila[4],
    }