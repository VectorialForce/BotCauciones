# Bot de Cauciones

> Bot de Telegram para monitorear tasas de cauciones en tiempo real desde PPI.

[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://t.me/caucho_bot)
[![Python](https://img.shields.io/badge/Python-3.9+-green?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## ¿Qué hace este bot?

Consulta las **tasas de cauciones** (1D, 2D, 3D y 7D) directamente desde la API de PPI y te permite configurar **alertas personalizadas** para recibir notificaciones cuando las tasas cambien.

### Características principales

- 📊 **Tasas en tiempo real** - Consulta tasas de 1, 2, 3 y 7 días desde PPI
- 🔔 **Alertas inteligentes** - Notificaciones solo cuando las tasas cambien según tu configuración
- 🕐 **Horario de mercado** - Respeta el horario del mercado argentino (Lun-Vie 10:30-16:30)
- 🇦🇷 **Timezone Argentina** - Todas las fechas en hora de Buenos Aires
- 💾 **Persistencia SQLite** - Tus preferencias se guardan entre reinicios
- ⚡ **Verificación cada 60s** - Monitoreo constante durante horario de mercado

## Tipos de Notificación

| Tipo | Descripción | Ideal para |
|------|-------------|------------|
| 🔔 **Cualquier cambio** | Notifica cada vez que las tasas varíen | Traders activos |
| 📊 **Umbral porcentual** | Solo cuando el cambio supere 0.5%, 1%, 2%, 5% o personalizado | Inversores que buscan movimientos significativos |

## 📱 Comandos

### `/start`
Mensaje de bienvenida con instrucciones y botones interactivos

### `/tasas`
Consultar tasas actuales con indicador de cambios

**Mercado abierto:**
```
📊 TASAS DE CAUCIONES

🕐 24H: 35.50% TNA 📈 +0.25% (+0.71%)
🕑 48H: 36.20% TNA 📉 -0.10% (-0.28%)
🕒 72H: 36.80% TNA

🕒 Actualizado: 2026-01-14 14:30:45
```

**Mercado cerrado:**
```
🔒 MERCADO CERRADO

📊 Últimas tasas registradas:

🕐 24H: 35.50% TNA
🕑 48H: 36.20% TNA
🕒 72H: 36.80% TNA

🕒 Actualizado: 2026-01-14 16:30:00

📅 Horario del mercado: Lun-Vie 10:30 - 16:30
```

### `/configurar`
Configurar tus preferencias de notificación

Muestra un menú interactivo con opciones:
- 🔔 Cualquier cambio
- 📊 Cambio > 0.5%
- 📊 Cambio > 1%
- 📊 Cambio > 2%
- 📊 Cambio > 5%
- ⚙️ Personalizado

### `/estado`
Ver tu configuración actual

Ejemplo de respuesta:
```
✅ Notificaciones activas

Tipo: 📊 Cambio > 1%
```

### `/pausar`
Pausar todas las notificaciones

### `/ayuda`
Ver lista de comandos

### `/stats` (Solo admin)
Ver estadísticas del bot

### `/export` (Solo admin)
Exportar backup de la base de datos

## 🚀 Instalación

### Requisitos
- Python 3.9+
- Cuenta PPI con acceso API
- Bot de Telegram (crear con @BotFather)

### Pasos

1. **Clonar repositorio:**
```bash
git clone https://github.com/VectorialForce/BotCauciones.git
cd BotCauciones
```

2. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

3. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

Variables requeridas:
```env
TELEGRAM_BOT_TOKEN=tu_token_de_telegram
PPI_PUBLIC_KEY=tu_public_key
PPI_SECRET_KEY=tu_secret_key
ADMIN_CHAT_ID=tu_chat_id  # Opcional, para comandos admin
```

4. **Ejecutar:**
```bash
python main.py
```

## ⚙️ Configuración Avanzada

### Horario del Mercado

En `main.py`, líneas 22-26:

```python
# Horario del mercado de cauciones (hora Argentina)
MARKET_OPEN_HOUR = 10
MARKET_OPEN_MINUTE = 30
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MINUTE = 30
```

### Cambiar intervalo de verificación

En `main.py`, dentro de `__init__`:

```python
self.check_interval = 60  # Verificar cada 60 segundos
```


### Tolerancia para detección de cambios

En `main.py`, método `calculate_changes`:

```python
'changed': abs(absolute_change) > 0.001  # Tolerancia para floats
```

## 🆘 Troubleshooting

| Problema | Solución |
|----------|----------|
| No recibo notificaciones | Verifica `/estado`, horario de mercado (10:30-16:30), y que tu umbral no sea muy alto |
| "Mercado Cerrado" | El mercado opera Lun-Vie 10:30-16:30. Fuera de horario muestra últimas tasas |
| Demasiadas notificaciones | Usa `/configurar` y selecciona un umbral más alto (2% o 5%) |

## 📄 Licencia

MIT License - [Ver licencia](LICENSE)
