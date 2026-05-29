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
        
        mensaje += f'\n💰 Volumen: {volumen}\n'
        mensaje += "\n"

    mensaje += f"🗓️  Actualizado: {tasas['timestamp']}"

    if not mercado_cerrado:
        mensaje += "\n\n📅 *Horario del mercado:* Lun-Vie 10:30 - 17:00"

    return mensaje

def bot_configurado(tasa_personalizada: bool, tasa: int = 0) -> str:
    if tasa_personalizada:
        descripcion = f"Vas a recibir notificaciones cuando las tasas cambien más de {tasa}%"
        cierre = f"Voy a avisarte cuando cambien más de {tasa}%"
    else:
        descripcion = "Vas a recibir notificaciones cada vez que las tasas cambien."
        cierre = "Voy a avisarte cuando cambien."

    return (
        f"✅ *¡Listo!*\n\n"
        f"{descripcion}\n\n"
        f"🎯 *Próximos pasos:*\n"
        f"• Usa /tasas para ver las tasas actuales\n"
        f"• Usa /estado para verificar tu configuración\n"
        f"• Usa /pausar si queres desactivar las alertas\n\n"
        f"El bot está monitoreando las tasas cada minuto. {cierre}"
    )