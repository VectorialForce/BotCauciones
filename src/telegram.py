from os import getenv
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

try:
    from .bot import mercado_abierto, calcular_cambios_en_tasas, get_tasas_caucion
    from . import database
    from . import twitter
    from .config import configurar_logging, HUSO_HORARIO_ARG, CIERRE_MERVAL
    from . import templates
except ImportError:
    from bot import mercado_abierto, calcular_cambios_en_tasas, get_tasas_caucion
    import database
    import twitter
    from config import configurar_logging, HUSO_HORARIO_ARG, CIERRE_MERVAL
    import templates

#----------------------------------------
# Config basica
#----------------------------------------

test = True

if test:
    telegram_token = getenv('TELEGRAM_BOT_TOKEN_TEST')
else:
    telegram_token = getenv('TELEGRAM_BOT_TOKEN')

admin_chat_id = int(getenv("ADMIN_CHAT_ID", "0"))
twitter_habilitado = getenv("TWITTER_ENABLED", "false").lower() == "true"

logger = configurar_logging()

#----------------------------------------
# Tipos de subscripción
#----------------------------------------

class TipoSubscripcion(Enum):
    NINGUNA = "none"
    CUALQUIER_CAMBIO = "any_change"
    POR_PORCENTAJE = "percentage"
    POR_OBJETIVO = "target"

@dataclass
class Suscripcion:
    chat_id: int
    subscription_type: TipoSubscripcion
    # % de cambio si es POR_PORCENTAJE, valor de tasa objetivo si es POR_OBJETIVO
    threshold_percentage: float = 0.0

#----------------------------------------
# Estado en memoria
#----------------------------------------

suscripciones: dict[int, Suscripcion] = {}
ultimas_tasas: dict | None = None
hora_inicio = datetime.now(HUSO_HORARIO_ARG)
estadisticas_sesion = {
    'checks': 0,
    'cambios_detectados': 0,
    'notificaciones_enviadas': 0,
    'notificaciones_fallidas': 0,
    'errores_api': 0,
    'comandos_procesados': 0,
}

#----------------------------------------
# Métodos PRIVADOS
#----------------------------------------

def _log_botones(command: str, chat_id: int, extra: str = ""):
    """Imprimir detalles de comandos ejecutados por los usuarios"""
    estadisticas_sesion['comandos_procesados'] += 1
    extra_info = f" | {extra}" if extra else ""
    logger.info(f"[COMANDO] /{command} | user={chat_id}{extra_info}")

def _cargar_suscripciones() -> dict[int, Suscripcion]:
    """Cargar suscripciones desde la base de datos al formato en memoria"""
    crudo = database.get_suscripciones() or {}
    return {
        chat_id: Suscripcion(
            chat_id=fila['chat_id'],
            subscription_type=TipoSubscripcion(fila['subscription_type']),
            threshold_percentage=fila['threshold_percentage'],
        )
        for chat_id, fila in crudo.items()
    }

def _texto_config_actual(suscripcion: Suscripcion) -> str:
    if suscripcion.subscription_type == TipoSubscripcion.CUALQUIER_CAMBIO:
        return "🔔 Notificaciones: Cualquier cambio"
    if suscripcion.subscription_type == TipoSubscripcion.POR_PORCENTAJE:
        return f"📊 Notificaciones: Cambios > {suscripcion.threshold_percentage}%"
    if suscripcion.subscription_type == TipoSubscripcion.POR_OBJETIVO:
        return f"🎯 Notificaciones: Cuando la tasa 1D llegue a {suscripcion.threshold_percentage}%"
    return "⏸️ Sin notificaciones activas"

def _teclado_bienvenida() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Ver tasas actuales", callback_data="quick_tasas")],
        [InlineKeyboardButton("🔔 Configurar alertas", callback_data="quick_config")],
        [InlineKeyboardButton("ℹ️ Ver todos los comandos", callback_data="quick_help")],
    ])

def _teclado_configurar() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔔 Cualquier cambio", callback_data="config_cualquier_cambio")],
        [
            InlineKeyboardButton("📊 Cambio > 0.5%", callback_data="config_porcentaje_0.5"),
            InlineKeyboardButton("📊 Cambio > 1%", callback_data="config_porcentaje_1.0"),
        ],
        [
            InlineKeyboardButton("📊 Cambio > 2%", callback_data="config_porcentaje_2.0"),
            InlineKeyboardButton("📊 Cambio > 5%", callback_data="config_porcentaje_5.0"),
        ],
        [InlineKeyboardButton("⚙️ Porcentaje personalizado", callback_data="config_porcentaje_custom")],
        [InlineKeyboardButton("🎯 Cuando llegue a un valor", callback_data="config_objetivo_custom")],
    ])

def _bienvenida_para(chat_id: int) -> tuple[str, InlineKeyboardMarkup | None]:
    if chat_id not in suscripciones:
        return templates.bienvenida(), _teclado_bienvenida()
    return templates.bienvenido_de_nuevo(_texto_config_actual(suscripciones[chat_id])), None

def _se_debe_notificar(suscripcion: Suscripcion, cambios: dict) -> bool:
    """Determinar si se debe notificar al usuario basado en su configuración"""
    if suscripcion.subscription_type == TipoSubscripcion.NINGUNA:
        return False

    if suscripcion.subscription_type == TipoSubscripcion.CUALQUIER_CAMBIO:
        return any(cambios[periodo]['changed'] for periodo in cambios)

    if suscripcion.subscription_type == TipoSubscripcion.POR_PORCENTAJE:
        return any(
            cambios[periodo]['changed'] and abs(cambios[periodo]['absolute']) >= suscripcion.threshold_percentage
            for periodo in cambios
        )

    if suscripcion.subscription_type == TipoSubscripcion.POR_OBJETIVO:
        objetivo = suscripcion.threshold_percentage
        info = cambios.get('1d')
        if not info or 'old' not in info or 'new' not in info:
            return False
        anterior, nuevo = info['old'], info['new']
        return (anterior < objetivo <= nuevo) or (anterior > objetivo >= nuevo)

    return False

async def _boton_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    chat_id = update.effective_chat.id
    _log_botones("start", chat_id, "nuevo" if chat_id not in suscripciones else "existente")

    texto, teclado = _bienvenida_para(chat_id)
    await update.message.reply_text(texto, reply_markup=teclado, parse_mode='Markdown')

async def _boton_tasas(update: Update, _context: ContextTypes.DEFAULT_TYPE):
        """Boton /tasas - Muestra las tasas desde la base de datos"""

        # Imprimir log
        _log_botones("tasas", update.effective_chat.id)

        # Leer las últimas tasas de la base de datos
        tasas = database.get_ultimas_tasas()

        if not tasas:
            await update.message.reply_text(
                "❌ No hay tasas registradas aún.\n\n"
                "El bot registra tasas automáticamente durante el horario de mercado (Lun-Vie 10:30-17:00).",
                parse_mode='Markdown'
            )
            return

        mensaje = templates.mensaje_tasas(tasas, mercado_cerrado=not mercado_abierto())

        await update.message.reply_text(mensaje, parse_mode='Markdown')

async def _boton_configurar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /configurar - Mostrar opciones de configuración"""
    _log_botones("configurar", update.effective_chat.id)
    await update.message.reply_text(
        templates.mensaje_configurar(),
        reply_markup=_teclado_configurar(),
        parse_mode='Markdown'
    )

async def _boton_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /estado - Mostrar configuración actual"""
    chat_id = update.effective_chat.id
    _log_botones("estado", chat_id)

    if chat_id not in suscripciones:
        mensaje = templates.mensaje_sin_notificaciones()
    else:
        mensaje = templates.mensaje_estado(_texto_config_actual(suscripciones[chat_id]))

    await update.message.reply_text(mensaje, parse_mode='Markdown')

async def _boton_pausar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /pausar - Desactivar notificaciones"""
    chat_id = update.effective_chat.id
    _log_botones("pausar", chat_id)

    if chat_id in suscripciones:
        del suscripciones[chat_id]
        await database.borrar_suscripcion(chat_id)
        await update.message.reply_text(templates.mensaje_pausado(), parse_mode='Markdown')
    else:
        await update.message.reply_text(templates.mensaje_sin_notificaciones_pausar())

async def _boton_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ayuda"""
    _log_botones("ayuda", update.effective_chat.id)
    await update.message.reply_text(templates.ayuda(), parse_mode='Markdown')

async def _boton_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /info"""
    _log_botones("info", update.effective_chat.id)
    await update.message.reply_text(templates.info(), parse_mode='Markdown', disable_web_page_preview=True)

async def _boton_sugerencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /sugerencia - Iniciar flujo para enviar sugerencia"""
    _log_botones("sugerencia", update.effective_chat.id)
    context.user_data['esperando_sugerencia'] = True
    await update.message.reply_text(templates.prompt_sugerencia(), parse_mode='Markdown')

async def _boton_sugerencias(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /sugerencias - Ver sugerencias (solo admin)"""
    chat_id = update.effective_chat.id
    if admin_chat_id != 0 and chat_id != admin_chat_id:
        await update.message.reply_text(templates.sin_permiso_admin())
        return

    sugerencias = database.get_sugerencias(no_leido=False)

    if not sugerencias:
        await update.message.reply_text("📭 No hay sugerencias registradas.")
        return

    await update.message.reply_text(templates.mensaje_sugerencias(sugerencias), parse_mode='Markdown')

    for s in sugerencias[:10]:
        if not s['read']:
            database.marcar_sugerencia_como_leida(s['id'])

async def _boton_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /stats - Ver estadísticas del bot (solo admin)"""
    chat_id = update.effective_chat.id
    if admin_chat_id != 0 and chat_id != admin_chat_id:
        await update.message.reply_text(templates.sin_permiso_admin())
        return

    try:
        stats = database.get_estadisticas()
        stats_subs = database.get_estadisticas_suscripciones()
        await update.message.reply_text(templates.mensaje_stats(stats, stats_subs), parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error en /stats: {e}")
        await update.message.reply_text(f"❌ Error obteniendo estadísticas: {e}")

async def _boton_dbstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /dbstatus - Verificar estado de la base de datos (solo admin)"""
    chat_id = update.effective_chat.id
    if admin_chat_id != 0 and chat_id != admin_chat_id:
        await update.message.reply_text(templates.sin_permiso_admin())
        return

    try:
        database.verificar_conexion()
        await update.message.reply_text(templates.mensaje_dbstatus(True), parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(templates.mensaje_dbstatus(False, str(e)), parse_mode='Markdown')

async def _boton_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /broadcast - Enviar mensaje a todos los suscriptores (solo admin)"""
    chat_id = update.effective_chat.id
    if admin_chat_id == 0 or chat_id != admin_chat_id:
        await update.message.reply_text(templates.sin_permiso_admin())
        return

    if not context.args:
        await update.message.reply_text(templates.mensaje_broadcast_uso(), parse_mode='Markdown')
        return

    texto = ' '.join(context.args)
    await update.message.reply_text(templates.mensaje_broadcast_enviando(len(suscripciones)))

    enviados = 0
    fallidos = 0
    bloqueados = []

    for cid in list(suscripciones.keys()):
        try:
            await context.bot.send_message(chat_id=cid, text=f"📢 Mensaje del administrador:\n\n{texto}")
            enviados += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            fallidos += 1
            if "bot was blocked" in str(e).lower():
                bloqueados.append(cid)
            logger.warning(f"[BROADCAST] Error enviando a {cid}: {e}")

    for cid in bloqueados:
        if cid in suscripciones:
            del suscripciones[cid]
            await database.borrar_suscripcion(cid)

    logger.info(f"[BROADCAST] Enviados: {enviados} | Fallidos: {fallidos} | Bloqueados: {len(bloqueados)}")

    await update.message.reply_text(
        templates.mensaje_broadcast_resultado(enviados, fallidos, len(bloqueados)),
        parse_mode='Markdown'
    )

async def _callback_botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejar callbacks de botones inline"""
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    data = query.data

    if data == "quick_tasas":
        tasas = database.get_ultimas_tasas()
        if not tasas:
            mensaje = (
                "❌ No hay tasas registradas aún.\n\n"
                "El bot registra tasas automáticamente durante el horario de mercado."
            )
        else:
            mensaje = templates.mensaje_tasas(tasas, mercado_cerrado=not mercado_abierto())
            mensaje += "\n\n💡 *Tip:* Usa /configurar para recibir alertas cuando cambien"
        await query.edit_message_text(mensaje, parse_mode='Markdown')
        return

    if data == "quick_config":
        await query.edit_message_text(
            templates.mensaje_configurar(),
            reply_markup=_teclado_configurar(),
            parse_mode='Markdown'
        )
        return

    if data == "quick_help":
        await query.edit_message_text(templates.ayuda(), parse_mode='Markdown')
        return

    if data == "config_cualquier_cambio":
        suscripcion = Suscripcion(chat_id=chat_id, subscription_type=TipoSubscripcion.CUALQUIER_CAMBIO)
        suscripciones[chat_id] = suscripcion
        await database.set_suscripcion(suscripcion)
        await query.edit_message_text(templates.bot_configurado('cualquier_cambio'), parse_mode='Markdown')
        logger.info(f"[CONFIG] user={chat_id} | tipo=cualquier_cambio")
        return

    if data.startswith("config_porcentaje_") and data != "config_porcentaje_custom":
        porcentaje = float(data.replace("config_porcentaje_", ""))
        suscripcion = Suscripcion(
            chat_id=chat_id,
            subscription_type=TipoSubscripcion.POR_PORCENTAJE,
            threshold_percentage=porcentaje
        )
        suscripciones[chat_id] = suscripcion
        await database.set_suscripcion(suscripcion)
        await query.edit_message_text(templates.bot_configurado('porcentaje', porcentaje), parse_mode='Markdown')
        logger.info(f"[CONFIG] user={chat_id} | tipo=porcentaje | umbral={porcentaje}%")
        return

    if data == "config_porcentaje_custom":
        await query.edit_message_text(templates.prompt_umbral_personalizado(), parse_mode='Markdown')
        context.user_data['esperando_umbral_porcentaje'] = True
        return

    if data == "config_objetivo_custom":
        await query.edit_message_text(templates.prompt_valor_objetivo(), parse_mode='Markdown')
        context.user_data['esperando_valor_objetivo'] = True
        return

async def _procesar_umbral_porcentaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        porcentaje = float(update.message.text.strip().replace(',', '.'))

        if porcentaje < 0 or porcentaje > 100:
            await update.message.reply_text(templates.error_umbral_invalido(), parse_mode='Markdown')
            return

        chat_id = update.effective_chat.id
        suscripcion = Suscripcion(
            chat_id=chat_id,
            subscription_type=TipoSubscripcion.POR_PORCENTAJE,
            threshold_percentage=porcentaje
        )
        suscripciones[chat_id] = suscripcion
        await database.set_suscripcion(suscripcion)

        await update.message.reply_text(templates.bot_configurado('porcentaje', porcentaje), parse_mode='Markdown')
        context.user_data['esperando_umbral_porcentaje'] = False
        logger.info(f"[CONFIG] user={chat_id} | tipo=personalizado | umbral={porcentaje}%")

    except ValueError:
        await update.message.reply_text(templates.error_umbral_no_numero(), parse_mode='Markdown')

async def _procesar_valor_objetivo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        objetivo = float(update.message.text.strip().replace(',', '.'))

        if objetivo < 0 or objetivo > 200:
            await update.message.reply_text(templates.error_objetivo_invalido(), parse_mode='Markdown')
            return

        chat_id = update.effective_chat.id
        suscripcion = Suscripcion(
            chat_id=chat_id,
            subscription_type=TipoSubscripcion.POR_OBJETIVO,
            threshold_percentage=objetivo
        )
        suscripciones[chat_id] = suscripcion
        await database.set_suscripcion(suscripcion)

        await update.message.reply_text(templates.bot_configurado('objetivo', objetivo), parse_mode='Markdown')
        context.user_data['esperando_valor_objetivo'] = False
        logger.info(f"[CONFIG] user={chat_id} | tipo=objetivo | valor={objetivo}%")

    except ValueError:
        await update.message.reply_text(templates.error_objetivo_no_numero(), parse_mode='Markdown')

async def _procesar_sugerencia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    username = update.effective_user.username
    texto = update.message.text.strip()

    if len(texto) < 5:
        await update.message.reply_text(templates.error_sugerencia_corta(), parse_mode='Markdown')
        return

    await database.set_sugerencia(chat_id, username, texto)
    await update.message.reply_text(templates.agradecimiento_sugerencia(), parse_mode='Markdown')
    context.user_data['esperando_sugerencia'] = False

async def _manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Manejar mensajes de texto (umbral/objetivo personalizado, sugerencias o mensajes no reconocidos)"""
    if context.user_data.get('esperando_umbral_porcentaje'):
        await _procesar_umbral_porcentaje(update, context)
    elif context.user_data.get('esperando_valor_objetivo'):
        await _procesar_valor_objetivo(update, context)
    elif context.user_data.get('esperando_sugerencia'):
        await _procesar_sugerencia(update, context)
    else:
        texto, teclado = _bienvenida_para(update.effective_chat.id)
        await update.message.reply_text(texto, reply_markup=teclado, parse_mode='Markdown')

async def _verificar_tasas_y_notificar(context: ContextTypes.DEFAULT_TYPE):
    """Verificar tasas periódicamente, guardar en DB y notificar cambios"""
    global ultimas_tasas

    if not mercado_abierto():
        return

    nuevas_tasas = get_tasas_caucion()

    if not nuevas_tasas:
        logger.error("[TASAS] Error obteniendo tasas de PPI")
        estadisticas_sesion['errores_api'] += 1
        return

    database.set_tasas(nuevas_tasas)
    estadisticas_sesion['checks'] += 1

    if not ultimas_tasas:
        ultimas_tasas = nuevas_tasas
        logger.info(f"[TASAS] Iniciales: 1D={nuevas_tasas['1d']:.2f}% | 7D={nuevas_tasas['7d']:.2f}%")
        return

    cambios = calcular_cambios_en_tasas(ultimas_tasas, nuevas_tasas)
    hay_cambios = any(cambios[periodo]['changed'] for periodo in cambios)

    if not hay_cambios:
        ultimas_tasas = nuevas_tasas
        return

    estadisticas_sesion['cambios_detectados'] += 1

    if twitter_habilitado and twitter.debe_tuitear(cambios):
        try:
            texto_tweet = templates.mensaje_tweet(nuevas_tasas, cambios)
            twitter.tuitear(texto_tweet)
        except Exception as e:
            logger.error(f"[TWITTER] Error en publicación: {e}")

    notificados = 0
    for chat_id, suscripcion in list(suscripciones.items()):
        if _se_debe_notificar(suscripcion, cambios):
            try:
                mensaje = templates.mensaje_notificacion_cambio(nuevas_tasas, cambios)
                await context.bot.send_message(chat_id=chat_id, text=mensaje, parse_mode='Markdown')
                notificados += 1
                estadisticas_sesion['notificaciones_enviadas'] += 1
            except Exception as e:
                logger.warning(f"[NOTIFY] Error enviando a {chat_id}: {e}")
                estadisticas_sesion['notificaciones_fallidas'] += 1
                if "bot was blocked" in str(e).lower():
                    del suscripciones[chat_id]
                    logger.info(f"[USERS] Usuario {chat_id} removido (bot bloqueado)")

    if notificados > 0:
        logger.info(f"[NOTIFY] {notificados} notificaciones enviadas")

    ultimas_tasas = nuevas_tasas

async def _job_tasas_cierre(context: ContextTypes.DEFAULT_TYPE):
    """Job programado para obtener las tasas al cierre del mercado"""
    global ultimas_tasas

    logger.info("[JOB] Ejecutando consulta de cierre")
    tasas = get_tasas_caucion()
    if tasas:
        database.set_tasas(tasas)
        ultimas_tasas = tasas
        logger.info(f"[JOB] Tasas de cierre: 1D={tasas['1d']:.2f}% | 7D={tasas['7d']:.2f}%")

async def _job_estado_log(context: ContextTypes.DEFAULT_TYPE):
    """Job periódico para loguear el estado del bot"""
    uptime = datetime.now(HUSO_HORARIO_ARG) - hora_inicio
    horas, resto = divmod(int(uptime.total_seconds()), 3600)
    minutos, _ = divmod(resto, 60)

    estado_mercado = "ABIERTO" if mercado_abierto() else "CERRADO"
    info_tasas = f"1D={ultimas_tasas['1d']:.2f}%" if ultimas_tasas else "N/A"

    logger.info(
        f"[STATUS] Uptime: {horas}h{minutos}m | "
        f"Mercado: {estado_mercado} | "
        f"Subs: {len(suscripciones)} | "
        f"Checks: {estadisticas_sesion['checks']} | "
        f"Cambios: {estadisticas_sesion['cambios_detectados']} | "
        f"Notif: {estadisticas_sesion['notificaciones_enviadas']} | "
        f"Tasa: {info_tasas}"
    )

async def _post_init(application: Application):
    """Inicialización post-startup"""
    global suscripciones, ultimas_tasas

    suscripciones = _cargar_suscripciones()
    ultimas_tasas = database.get_ultimas_tasas()
    logger.info(f"[INIT] Suscriptores activos: {len(suscripciones)}")

    if application.job_queue:
        # Job de verificación de tasas (cada 60 segundos)
        application.job_queue.run_repeating(_verificar_tasas_y_notificar, interval=60, first=10)

        # Job de status (cada 15 minutos)
        application.job_queue.run_repeating(_job_estado_log, interval=900, first=60)

        # Job diario al cierre del mercado
        hora_cierre = CIERRE_MERVAL.replace(tzinfo=HUSO_HORARIO_ARG)
        application.job_queue.run_daily(_job_tasas_cierre, time=hora_cierre, days=(0, 1, 2, 3, 4))

        logger.info("[JOBS] Configurados: tasas(60s), status(15m), cierre")
    else:
        logger.warning("JobQueue no disponible - las notificaciones automáticas no funcionarán")

#----------------------------------------
# Métodos PUBLICOS
#----------------------------------------

def activar_caucho_bot():
    """Levantar bot. Mantener funcion activa SIEMPRE"""

    # Crear aplicación con post_init
    application = (
        Application.builder()
        .token(telegram_token)
        .post_init(_post_init)
        .build()
    )

    # Agregar handlers de comandos
    application.add_handler(CommandHandler("start", _boton_start))
    application.add_handler(CommandHandler("tasas", _boton_tasas))
    application.add_handler(CommandHandler("configurar", _boton_configurar))
    application.add_handler(CommandHandler("estado", _boton_estado))
    application.add_handler(CommandHandler("pausar", _boton_pausar))
    application.add_handler(CommandHandler("ayuda", _boton_ayuda))
    application.add_handler(CommandHandler("info", _boton_info))
    application.add_handler(CommandHandler("sugerencia", _boton_sugerencia))
    application.add_handler(CommandHandler("sugerencias", _boton_sugerencias))
    application.add_handler(CommandHandler("stats", _boton_stats))
    application.add_handler(CommandHandler("dbstatus", _boton_dbstatus))
    application.add_handler(CommandHandler("broadcast", _boton_broadcast))

    # Agregar handler para botones inline
    application.add_handler(CallbackQueryHandler(_callback_botones))

    # Agregar handler para mensajes de texto
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _manejar_mensaje))

    # Iniciar bot
    logger.info("Bot iniciado...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
