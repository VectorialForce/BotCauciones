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

def _obtener_estadisticas() -> dict:
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

            

def get_ultima_tasa() -> dict | None:
    with conectar_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT rate_1d, rate_2d, rate_3d, rate_7d, timestamp
                FROM rate_history
                ORDER BY id DESC
                LIMIT 1
            """)
            row = cur.fetchone()

    if row is None:
        return None

    return {
        '1d': row[0],
        '2d': row[1],
        '3d': row[2],
        '7d': row[3],
        'timestamp': row[4],
    }

tasa = get_ultima_tasa()
print(tasa)