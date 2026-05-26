import asyncio
from contextlib import contextmanager
from dotenv import load_dotenv
from os import getenv
import psycopg2
from psycopg2.extras import RealDictCursor
from config import configurar_logging

#----------------------------------------
# Config basica
#----------------------------------------

# IMPORTANTE - Bandera para apuntar a test o prod
test = False

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

write_lock = asyncio.Lock()

@contextmanager
def conectar_db():
    """Conectar a la base de datos"""
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
        raise ConnectionError(f"No se pudo conectar a la base de datos: {e}")
    except Exception as e:
        logger.error(f"No se pudo conectar a PostgreSQL: {e}")
        raise

#----------------------------------------
# GETTERS y SETTERS
#----------------------------------------

def get_estadisticas() -> dict:
    """Obtener cantidad de suscripciones, cantidad de sugerencias y tamaño de la base de datos"""

    tablas = ['subscriptions', 'suggestions']
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
    try:
        with conectar_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
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
    except Exception as e:
        logger.error(f"Error cargando suscripciones: {e}")
        return None

def get_ultimas_tasas() -> dict | None:
    """Obtener últimas tasas registradas"""
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

def get_sugerencias(no_leido: bool = False) -> list:
    """Obtener sugerencias de la base de datos"""
    with conectar_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            query = "SELECT * FROM suggestions"
            if no_leido:
                query += " WHERE read = FALSE"
            query += " ORDER BY created_at DESC LIMIT 20"
            cur.execute(query)
            
            return [dict(row) for row in cur.fetchall()]


#----------------------------------------
# Métodos PUBLICOS
#----------------------------------------

async def guardar_suscripcion(suscripcion):
    """Guardar o actualizar una suscripción (async)"""
    async with write_lock:
        with conectar_db() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO subscriptions
                    (chat_id, subscription_type, threshold_percentage, updated_at)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (chat_id) DO UPDATE SET
                    subscription_type = EXCLUDED.subscription_type,
                    threshold_percentage = EXCLUDED.threshold_percentage,
                    updated_at = CURRENT_TIMESTAMP
                """, (
                suscripcion.chat_id,
                suscripcion.subscription_type.value,
                suscripcion.threshold_percentage
                ))
                conn.commit()

        logger.debug(f"💾 Suscripción guardada: chat_id={suscripcion.chat_id}")

async def borrar_suscripcion(chat_id: int):
    """Eliminar una suscripción"""
    async with write_lock:
        with conectar_db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM subscriptions WHERE chat_id = %s", (chat_id,))
                conn.commit()

        logger.info(f"🗑️ Suscripción eliminada: chat_id={chat_id}")

def guardar_tasas(tasas: dict):
    """Guardar tasas en la base de datos"""
    with conectar_db() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO rate_history (rate_1d, rate_2d, rate_3d, rate_7d, timestamp)
                VALUES (%s, %s, %s, %s, %s)
            """, (tasas['1d'], tasas['2d'], tasas['3d'], tasas['7d'], tasas['timestamp']))
            conn.commit()
        
        logger.debug(f"💾 Tasas guardadas en DB: {tasas}")

async def guardar_sugerencia(chat_id:int, username: str, mensaje: str):
    """Guardar una sugerencia en la base de datos"""
    async with write_lock:
        with conectar_db() as conn:
            with conn.cursor() as cur:
               cur.execute("""
                    INSERT INTO suggestions (chat_id, username, message)
                    VALUES (%s, %s, %s)
                    """, (chat_id, username, mensaje))
            conn.commit()
        
        logger.info(f"💬 Sugerencia guardada de chat_id={chat_id}")

def marcar_sugerencia_como_leida(sugerencia_id: int):
    """Marcar una sugerencia como leída"""
    with conectar_db() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE suggestions SET read = TRUE WHERE id = %s", (sugerencia_id,))
            conn.commit()