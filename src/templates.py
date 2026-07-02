def bienvenida() -> str:
    return (
        '👋 *¡Hola! Soy @caucho_bot*\n\n'
        'Te ayudo a monitorear las tasas de cauciones en tiempo real.\n\n'
        '🎯 *¿Qué puedo hacer por vos?*\n\n'
        '📊 *Ver tasas actuales*\n'
        'Usa /tasas para consultar las tasas de 1, 2, 3 y 7 días\n\n'
        '🔔 *Recibir alertas automáticas*\n'
        'Te notifico cuando las tasas cambien. Podes elegir:\n'
        '  • Cualquier variación\n'
        '  • Solo cambios importantes (>1%, >2%, etc.)\n'
        '  • Cuando la tasa llegue a un valor que elijas (%25, %50, etc)\n'
        '¿Queres empezar? Elegi una opción:'
    )

def ayuda() -> str:
    return (
        "ℹ️ *Guía de Uso del Bot*\n\n"
        "*📊 Consultar tasas:*\n"
        "/tasas - Ver las tasas actuales de cauciones 1 día, 2 días, 3 días y 7 días\n\n"
        "*🔔 Configurar alertas:*\n"
        "/configurar - Elegir cuándo recibir notificaciones:\n"
        "  • Cualquier cambio en las tasas\n"
        "  • Solo cambios mayores a 0.5%, 1%, 2%, 5%\n"
        '  • Cuando la tasa llegue a un valor que elijas (%25, %50, etc)\n'
        "  • Umbral personalizado\n\n"
        "*📱 Gestionar alertas:*\n"
        "/estado - Ver tu configuración actual\n"
        "/pausar - Desactivar alertas temporalmente\n\n"
        "*💬 Contacto:*\n"
        "/sugerencia - Enviar una sugerencia o comentario\n\n"
        "*💡 ¿Cómo funciona?*\n"
        "El bot verifica las tasas cada minuto. Cuando detecta un cambio, "
        "te notifica solo si cumple con tu configuración.\n\n"
        "*Ejemplo:*\n"
        "Si elegis \"Cambio > 1%\" y la tasa pasa de 35% a 35.4% (+1.14%), "
        "recibirás una alerta. Si cambia a 35.2% (+0.57%), no vas a recibir ninguna notificación.\n\n"
        "¿Necesitas ayuda? Envía /start para volver al menú principal"
    )

# Nombre temporal, no se me ocurre otra cosa
def bienvenido_de_nuevo(config_info: str) -> str:
    return (
        "👋 *¡Hola!*\n\n"
        f"{config_info}\n\n"
        "*Acciones rápidas:*\n"
        "• /tasas - Ver tasas actuales\n"
        "• /configurar - Cambiar alertas\n"
        "• /estado - Ver tu configuración\n"
        "• /pausar - Pausar notificaciones\n"
        "• /sugerencia - Enviar comentario\n"
        "• /info - Ver código fuente y miembros del equipo de CauchoBot\n"
    )

def info() -> str:
    return (
        "ℹ️ *CauchoBot* es una iniciativa para fomentar el uso de scripts en el mercado Argentino\n\n"
        "📂 *Código fuente:*\n"
        "[Ver en GitHub](https://github.com/VectorialForce/botCauciones)\n"
        "💼 *Contacto:*\n"
        "[LinkedIn](https://ar.linkedin.com/in/leonel-agustin-perez)\n"
        "☕ *Apoyá el proyecto:*\n"
        "Si queres colaborar con el mantenimiento del bot, podés invitarme un cafecito:\n"
        "[Cafecito](https://cafecito.app/leonel-perez)"
    )

def agradecimiento_sugerencia() -> str:
    return (
        "✅ *¡Gracias por tu sugerencia!*\n\n"
        "Tu mensaje fue registrado correctamente.\n\n"
        "Agradecemos tu feedback para mejorar el bot."
    )

#Trabajar mensaje, no me convence el formato actual
def mensaje_tasas(tasas: dict, mercado_cerrado: bool, cambios: dict = None) -> str:
    '''Verif'''
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
        
        mensaje += f'\n💰 Volumen: {volumen:,}'.replace(",", ".") + '\n'
        mensaje += "\n"

    mensaje += f"🗓️  Actualizado: {tasas['timestamp']}"

    if mercado_cerrado:
        mensaje += "\n\n📅 *Horario del mercado:* Lun-Vie 10:30 - 17:00"

    return mensaje

def bot_configurado(tipo: str, valor: float = 0.0) -> str:
    if tipo == 'cualquier_cambio':
        descripcion = "Vas a recibir notificaciones cada vez que las tasas cambien."
        cierre = "Voy a avisarte cuando cambien."
    elif tipo == 'porcentaje':
        descripcion = f"Vas a recibir notificaciones cuando las tasas cambien más de {valor}%"
        cierre = f"Voy a avisarte cuando cambien más de {valor}%"
    else:  # objetivo
        descripcion = f"Vas a recibir una notificación cuando la tasa 1D llegue a {valor}%"
        cierre = f"Voy a avisarte apenas la tasa 1D llegue a {valor}%"

    return (
        f"✅ *¡Listo!*\n\n"
        f"{descripcion}\n\n"
        f"🎯 *Próximos pasos:*\n"
        f"• Usa /tasas para ver las tasas actuales\n"
        f"• Usa /estado para verificar tu configuración\n"
        f"• Usa /pausar si queres desactivar las alertas\n\n"
        f"El bot está monitoreando las tasas cada minuto. {cierre}"
    )

def mensaje_notificacion_cambio(tasas: dict, cambios: dict) -> str:
    return "🔔 *¡Cambio en las tasas!*\n\n" + mensaje_tasas(tasas, mercado_cerrado=False, cambios=cambios)

def mensaje_configurar() -> str:
    return (
        "⚙️ *Configurar Notificaciones*\n\n"
        "Elegi cuándo queres recibir notificaciones:\n\n"
        "🔔 *Cualquier cambio* - Te aviso cada vez que las tasas varíen\n\n"
        "📊 *Cambio porcentual* - Solo cuando el cambio supere el % que elijas\n\n"
        "🎯 *Valor objetivo* - Te aviso cuando la tasa 1D llegue al valor que elijas\n\n"
        "Selecciona una opción:"
    )

def mensaje_estado(config_info: str) -> str:
    return f"✅ *Notificaciones activas*\n\n{config_info}"

def mensaje_sin_notificaciones() -> str:
    return "ℹ️ No tenes notificaciones activas.\n\nUsa /configurar para activarlas."

def mensaje_pausado() -> str:
    return "⏸️ Notificaciones pausadas.\n\nUsa /configurar para reactivarlas."

def mensaje_sin_notificaciones_pausar() -> str:
    return "ℹ️ No tenes notificaciones activas"

def prompt_sugerencia() -> str:
    return (
        "💬 *Enviar Sugerencia*\n\n"
        "Escribí tu mensaje, sugerencia o comentario.\n\n"
        "📝 Puede ser:\n"
        "• Una idea para mejorar el bot\n"
        "• Un problema que encontraste\n"
        "• Cualquier comentario\n\n"
        "Envía tu mensaje:"
    )

def error_sugerencia_corta() -> str:
    return "❌ El mensaje es muy corto.\n\nPor favor escribí un mensaje más detallado:"

def prompt_umbral_personalizado() -> str:
    return (
        "⚙️ *Umbral Personalizado*\n\n"
        "Envía un número con el porcentaje que deseas.\n\n"
        "📝 *Ejemplos:*\n"
        "• `0.5` = Alertas cuando cambie más de 0.5%\n"
        "• `1.5` = Alertas cuando cambie más de 1.5%\n"
        "• `3` = Alertas cuando cambie más de 3%\n\n"
        "Envía tu número:"
    )

def error_umbral_invalido() -> str:
    return (
        "❌ El porcentaje debe estar entre 0 y 100.\n\n"
        "💡 *Tip:* Si queres alertas frecuentes, usa 0.5 o 1.\n"
        "Si solo queres cambios importantes, usa 2 o 5.\n\n"
        "Intenta de nuevo:"
    )

def error_umbral_no_numero() -> str:
    return (
        "❌ Por favor envia solo un número.\n\n"
        "📝 *Ejemplos válidos:*\n"
        "• 0.5\n• 1.5\n• 2\n• 5\n\n"
        "Intenta de nuevo:"
    )

def prompt_valor_objetivo() -> str:
    return (
        "🎯 *Valor Objetivo*\n\n"
        "Envía el valor de tasa (1 día) al que queres que te avise.\n\n"
        "📝 *Ejemplos:*\n"
        "• `25` = Avisar cuando la tasa llegue a 25%\n"
        "• `30.5` = Avisar cuando la tasa llegue a 30.5%\n\n"
        "Envía tu número:"
    )

def error_objetivo_invalido() -> str:
    return "❌ El valor debe estar entre 0 y 200.\n\nIntenta de nuevo:"

def error_objetivo_no_numero() -> str:
    return (
        "❌ Por favor envia solo un número.\n\n"
        "📝 *Ejemplos válidos:*\n"
        "• 25\n• 30.5\n\n"
        "Intenta de nuevo:"
    )

def sin_permiso_admin() -> str:
    return "⛔ Solo el administrador puede usar este comando"

def mensaje_sugerencias(sugerencias: list) -> str:
    mensaje = "💬 *Sugerencias recibidas:*\n\n"
    for s in sugerencias[:10]:
        status = "🆕" if not s['read'] else "✓"
        username = f"@{s['username']}" if s['username'] else f"ID:{s['chat_id']}"
        fecha = str(s['created_at'])[:16] if s['created_at'] else ""
        texto = s['message'][:100] + "..." if len(s['message']) > 100 else s['message']
        mensaje += f"{status} *{username}* ({fecha})\n{texto}\n\n"
    return mensaje

def mensaje_stats(stats: dict, stats_subs: dict) -> str:
    return (
        "📊 *Estadísticas del Bot*\n\n"
        f"👥 Total usuarios: {stats_subs.get('total_usuarios', 0)}\n"
        f"🔔 Cualquier cambio: {stats_subs.get('usuarios_cualquier_cambio', 0)}\n"
        f"📊 Con umbral: {stats_subs.get('usuarios_porcentaje', 0)}\n"
        f"🎯 Con objetivo: {stats_subs.get('usuarios_objetivo', 0)}\n"
        f"📈 Umbral promedio: {stats_subs.get('umbral_promedio', 0)}%\n\n"
        "🗄️ *Base de datos:* PostgreSQL\n"
        f"💾 Tamaño: {stats.get('tamanio_db', 'N/A')}\n"
        f"📝 Registros de tasas: {stats.get('rate_history_count', 'N/A')}\n"
        f"💬 Sugerencias: {stats.get('suggestions_count', 'N/A')}\n"
    )

def mensaje_dbstatus(ok: bool, detalle: str = "") -> str:
    if ok:
        return "🔍 *Estado de la Base de Datos*\n\n✅ Conexión verificada correctamente"
    return f"🔍 *Estado de la Base de Datos*\n\n❌ Error de conexión: {detalle}"

def mensaje_broadcast_uso() -> str:
    return (
        "📢 *Broadcast*\n\n"
        "Uso: `/broadcast <mensaje>`\n\n"
        "Ejemplo:\n"
        "`/broadcast Hola a todos! El bot estará en mantenimiento mañana.`"
    )

def mensaje_broadcast_enviando(cantidad: int) -> str:
    return f"📤 Enviando mensaje a {cantidad} suscriptores..."

def mensaje_broadcast_resultado(enviados: int, fallidos: int, bloqueados: int) -> str:
    return (
        "✅ *Broadcast completado*\n\n"
        f"📤 Enviados: {enviados}\n"
        f"❌ Fallidos: {fallidos}\n"
        f"🚫 Bloqueados (removidos): {bloqueados}"
    )