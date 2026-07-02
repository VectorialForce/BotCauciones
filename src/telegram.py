from os import getenv
from enum import Enum
from telegram import Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler

try:
    from .bot import mercado_abierto
    from .database import get_ultimas_tasas
    from .config import configurar_logging, HUSO_HORARIO_ARG, CIERRE_MERVAL, APERTURA_MERVAL
    from . import templates
except ImportError:
    from config import configurar_logging, HUSO_HORARIO_ARG, CIERRE_MERVAL, APERTURA_MERVAL
    import templates
    from bot import mercado_abierto
    from database import get_ultimas_tasas

#----------------------------------------
# Config basica
#----------------------------------------

test = True

if test:
    telegram_token = getenv('TELEGRAM_BOT_TOKEN_TEST')
else:
    telegram_token = getenv('TELEGRAM_BOT_TOKEN')

logger = configurar_logging()

#----------------------------------------
# Tipos de subscripción
#----------------------------------------

class TipoSubscripcion(Enum):
    NINGUNA = "none"
    CUALQUIER_CAMBIO = "cualquier_cambio"
    POR_PORCENTAJE = "porcentaje"
    POR_OBJETIVO = "objetivo"

@dataclass
class UserSubscription:
    chat_id: int
    subscription_type: SubscriptionType
    threshold_percentage: float = 0.0  # % de cambio para notificar

    def to_dict(self):
        return {
            'chat_id': self.chat_id,
            'subscription_type': self.subscription_type.value,
            'threshold_percentage': self.threshold_percentage
        }

    @staticmethod
    def from_dict(data):
        return UserSubscription(
            chat_id=data['chat_id'],
            subscription_type=SubscriptionType(data['subscription_type']),
            threshold_percentage=data.get('threshold_percentage', 0.0)
        )


#----------------------------------------
# Métodos PRIVADOS
#----------------------------------------

def _log_botones(command: str, chat_id: int, extra: str = ""):
    '''Imprimir detalles de comandos ejecutados por los usuarios'''
    extra_info = f" | {extra}" if extra else ""
    logger.info(f"[COMANDO] /{command} | user={chat_id}{extra_info}")

async def _boton_tasas(update: Update, _context: ContextTypes.DEFAULT_TYPE):
        """Boton /tasas - Muestra las tasas desde la base de datos"""
        
        # Imprimir log
        _log_botones("tasas", update.effective_chat.id)

        # Leer las últimas tasas de la base de datos
        tasas = get_ultimas_tasas()

        if not tasas:
            await update.message.reply_text(
                "❌ No hay tasas registradas aún.\n\n"
                "El bot registra tasas automáticamente durante el horario de mercado (Lun-Vie 10:30-17:00).",
                parse_mode='Markdown'
            )
            return

        mensaje = templates.mensaje_tasas(tasas, mercado_cerrado=not mercado_abierto())
        
        await update.message.reply_text(mensaje, parse_mode='Markdown')

#----------------------------------------
# Métodos PUBLICOS
#----------------------------------------

# Stub, no hace nada
def se_debe_notificar_al_usuario(suscripcion:TipoSubscripcion, cambios) -> bool:
    """Determinar si se debe notificar al usuario basado en su configuración"""

    # Cualquier variacion
    if suscripcion.CUALQUIER_CAMBIO:
        pass
    elif suscripcion.POR_OBJETIVO:
        pass
    elif suscripcion.POR_PORCENTAJE:
        pass
    else:
        pass

def activar_caucho_bot():
    """Levantar bot. Mantener funcion activa SIEMPRE"""

    # Crear aplicación con post_init y post_shutdown
    application = (
        Application.builder()
        .token(telegram_token)
        .build()
    )

    # Agregar handlers de comandos
    application.add_handler(CommandHandler("tasas", _boton_tasas))

    # Iniciar bot
    logger.info("Bot iniciado...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)