# Bot de Cauciones

> Bot de Telegram (con publicación automática en X/Twitter) para monitorear tasas de cauciones en tiempo real desde PPI.

[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://t.me/caucho_bot)
[![Python](https://img.shields.io/badge/Python-3.9+-green?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## ¿Qué hace este bot?

Consulta las **tasas de cauciones** (1D, 2D, 3D y 7D) y su **volumen operado** directamente desde la API de PPI, te permite configurar **alertas personalizadas** para recibir notificaciones cuando las tasas cambien, y publica automáticamente en X/Twitter ante subas relevantes.

### Características principales

- 📊 **Tasas en tiempo real** - Consulta tasas y volumen de 1, 2, 3 y 7 días desde PPI
- 🔔 **Alertas inteligentes** - Cualquier cambio, umbral porcentual o valor objetivo
- 🐦 **Publicación en X/Twitter** - Tuitea automáticamente cuando una tasa sube ≥ 5 puntos porcentuales
- 🕐 **Horario de mercado** - Respeta el horario del mercado argentino (Lun-Vie 10:30-17:00)
- 🇦🇷 **Timezone Argentina** - Todas las fechas en hora de Buenos Aires
- 💾 **Persistencia PostgreSQL** - Tasas, suscripciones y sugerencias en base de datos
- ⚡ **Verificación cada 60s** - Monitoreo constante durante horario de mercado
- 💬 **Sistema de sugerencias** - Los usuarios pueden dejar feedback con `/sugerencia`
- 🛠️ **Panel de administración** - Estadísticas, estado de la DB y broadcast a suscriptores
- 🧪 **Modo test** - Bot, token y base de datos separados para desarrollo (`TEST=true`)

## Tipos de Notificación

| Tipo | Descripción | Ideal para |
|------|-------------|------------|
| 🔔 **Cualquier cambio** | Notifica cada vez que las tasas varíen | Traders activos |
| 📊 **Umbral porcentual** | Solo cuando el cambio supere 0.5%, 1%, 2%, 5% o personalizado | Inversores que buscan movimientos significativos |
| 🎯 **Valor objetivo** | Notifica una única vez cuando la tasa 1D cruza el valor elegido (ej: 25%, 50%) | Quienes esperan un nivel de tasa específico |

## 📱 Comandos

### `/start`
Mensaje de bienvenida con instrucciones y botones interactivos (ver tasas, configurar alertas, ver ayuda)

### `/tasas`
Consultar tasas actuales (con volumen) e indicador de cambios

**Mercado abierto:**
```
📊 TASAS DE CAUCIONES

🕐 1D: 35.50% TNA 📈 +0.25%
💰 Volumen: 1.250.000

🕑 2D: 36.20% TNA 📉 -0.10%
💰 Volumen: 340.000

🕒 3D: 36.80% TNA
💰 Volumen: 90.000

🕒 7D: 37.10% TNA
💰 Volumen: 210.000

🗓️ Actualizado: 2026-08-04 14:30:45
```

**Mercado cerrado:**
```
🔒 MERCADO CERRADO

📊 Últimas tasas registradas:
...
📅 Horario del mercado: Lun-Vie 10:30 - 17:00
```

### `/configurar`
Configurar tus preferencias de notificación mediante un menú interactivo:
- 🔔 Cualquier cambio
- 📊 Cambio > 0.5%, 1%, 2%, 5% o personalizado
- 🎯 Cuando la tasa 1D llegue a un valor objetivo

### `/estado`
Ver tu configuración actual

### `/pausar`
Pausar todas las notificaciones

### `/ayuda`
Ver guía de uso y lista de comandos

### `/info`
Ver código fuente del proyecto y contacto del equipo

### `/sugerencia`
Enviar una sugerencia o comentario sobre el bot

### `/sugerencias` (Solo admin)
Ver las últimas sugerencias enviadas por los usuarios

### `/stats` (Solo admin)
Ver estadísticas del bot: suscriptores, sugerencias, tamaño de la base de datos, etc.

### `/dbstatus` (Solo admin)
Verificar la conexión a la base de datos

### `/broadcast <mensaje>` (Solo admin)
Enviar un mensaje a todos los suscriptores activos

## 🐦 Publicación automática en X/Twitter

Cuando una tasa sube 5 puntos porcentuales o más en una sola verificación, el bot publica automáticamente un tweet con el resumen de tasas usando Selenium (con perfil de Chrome persistente para mantener la sesión logueada). Se activa con `TWITTER_ENABLED=true`.

## 🚀 Instalación

### Requisitos
- Python 3.9+
- PostgreSQL
- Cuenta PPI con acceso API
- Bot de Telegram (crear con @BotFather)
- (Opcional) Chrome/Chromium con sesión de X/Twitter iniciada, para la publicación automática

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

Crear un archivo `.env` en la raíz del proyecto con:

```env
# Telegram
TELEGRAM_BOT_TOKEN=tu_token_de_telegram
TELEGRAM_BOT_TOKEN_TEST=tu_token_de_bot_de_test   # usado si TEST=true
ADMIN_CHAT_ID=tu_chat_id                          # para comandos de admin

# PPI
PPI_PUBLIC_KEY=tu_public_key
PPI_SECRET_KEY=tu_secret_key

# Base de datos (PostgreSQL)
DB_HOST=localhost
DB_PORT=5432
DB_USER=tu_usuario
DB_PASS=tu_password
DB_NAME=cauciones
DB_NAME_TEST=cauciones_test                       # usado si TEST=true

# Modo test (separa bot, token y DB de producción)
TEST=false

# X/Twitter (opcional)
TWITTER_ENABLED=false
CHROME_PROFILE_PATH=chrome_profile                 # perfil de Chrome con sesión iniciada
```

4. **Ejecutar:**
```bash
python main.py
```

### Con Docker

El proyecto incluye `Dockerfile` y `compose.yaml` (imagen con Chromium + Xvfb para soportar la publicación en Twitter):

```bash
docker compose up -d --build
```

El contenedor usa `network_mode: host` para acceder a PostgreSQL en otro servidor, y monta `./chrome_profile` como volumen para persistir la sesión de Twitter entre reinicios.

## ⚙️ Configuración Avanzada

### Horario del Mercado

En `src/config.py`:

```python
APERTURA_MERVAL = time(10, 30)
CIERRE_MERVAL = time(17, 0)
```

### Cambiar intervalo de verificación

En `src/bot.py`, dentro de `_post_init`:

```python
application.job_queue.run_repeating(_verificar_tasas_y_notificar, interval=60, first=10)
```

### Tolerancia para detección de cambios

En `src/bot.py`, función `calcular_cambios_en_tasas`:

```python
'changed': abs(variacion_absoluta) > 0.001  # Tolerancia para floats
```

### Umbral de publicación en Twitter

En `src/twitter.py`:

```python
UMBRAL_TWEET = 5.0  # Puntos porcentuales absolutos
```

## 📄 Licencia

MIT License - [Ver licencia](LICENSE)
