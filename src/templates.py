
def bienvenida() -> str:
    return (
        '👋 *¡Hola! Soy @caucho_bot*\n\n'
        'Te ayudo a monitorear las tasas de cauciones en tiempo real.\n\n'
        '🎯 *¿Qué puedo hacer por vos?*\n\n'
        '📊 *Ver tasas actuales*\n'
        'Usa /tasas para consultar las tasas de 1 día, 2 días, 3 días y 7 días\n\n'
        '🔔 *Recibir alertas automáticas*\n'
        'Te notifico cuando las tasas cambien. Puedes elegir:\n'
        '  • Cualquier variación\n'
        '  • Solo cambios importantes (>1%, >2%, etc.)\n\n'
        '¿Queres empezar? Elegi una opción:'
    )

# Nombre temporal, no se me ocurre otra cosa
def welcome_back(config_info: str) -> str:
    return (
        "👋 *¡Hola!*\n\n"
        f"{config_info}\n\n"
        "*Acciones rápidas:*\n"
        "• /tasas - Ver tasas actuales\n"
        "• /configurar - Cambiar alertas\n"
        "• /estado - Ver tu configuración\n"
        "• /pausar - Pausar notificaciones\n"
        "• /sugerencia - Enviar comentario\n"
    )

def agradecimiento_sugerencia() -> str:
    return (
        "✅ *¡Gracias por tu sugerencia!*\n\n"
        "Tu mensaje fue registrado correctamente.\n\n"
        "Aprecio tu feedback para mejorar el bot."
    )