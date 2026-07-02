from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
from os import getenv
from pathlib import Path
import time

try:
    from .config import configurar_logging
except ImportError:
    from config import configurar_logging

#----------------------------------------
# Config basica
#----------------------------------------

logger = configurar_logging()

UMBRAL_TWEET = 5.0  # Puntos porcentuales absolutos

driver = None

#----------------------------------------
# Métodos PRIVADOS
#----------------------------------------

def _iniciar_driver():
    """Inicializar ChromeDriver con stealth"""
    global driver

    options = webdriver.ChromeOptions()

    # Usar Chromium si está disponible (Docker ARM64), sino Chrome local
    service = None
    chromium_path = Path("/usr/bin/chromium")
    chromedriver_path = Path("/usr/bin/chromedriver")
    if chromium_path.exists():
        options.binary_location = str(chromium_path)
    if chromedriver_path.exists():
        service = Service(str(chromedriver_path))

    # Usar profile con sesión de Twitter pre-logueada
    chrome_profile_path = getenv("CHROME_PROFILE_PATH", "chrome_profile")
    profile_abs = str(Path(chrome_profile_path).resolve())
    options.add_argument(f"--user-data-dir={profile_abs}")

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=options, service=service) if service else webdriver.Chrome(options=options)

    stealth(
        driver,
        languages=["es-AR", "es"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    logger.info("[TWITTER] ChromeDriver inicializado con stealth")

#----------------------------------------
# Métodos PUBLICOS
#----------------------------------------

def debe_tuitear(cambios: dict) -> bool:
    """Determinar si se debe twittear (suba >= 5pp en cualquier período)"""
    if not cambios:
        return False

    for periodo in cambios:
        if cambios[periodo]['changed'] and cambios[periodo]['absolute'] >= UMBRAL_TWEET:
            return True
    return False

def formatear_tweet(tasas: dict, cambios: dict) -> str:
    """Formatear mensaje para Twitter (plain-text, sin markdown)"""
    mensaje = "🔔 ¡Cambio en las tasas!\n\n"
    mensaje += "📊 TASAS DE CAUCIONES\n\n"

    for periodo, etiqueta in [('1d', '🕐'), ('2d', '🕑'), ('3d', '🕒'), ('7d', '🕒')]:
        tasa = tasas[periodo]
        mensaje += f"{etiqueta} {periodo.upper()}: {tasa:.2f}% TNA"

        if cambios and periodo in cambios and cambios[periodo]['changed']:
            cambio = cambios[periodo]
            flecha = "📈" if cambio['absolute'] > 0 else "📉"
            signo = "+" if cambio['absolute'] > 0 else ""
            mensaje += f" {flecha} {signo}{cambio['absolute']:.2f}%"

        mensaje += "\n"

    mensaje += f"\n🕒 Actualizado: {tasas['timestamp']}"

    return mensaje

def tuitear(texto: str) -> bool:
    """Publicar un tweet usando Selenium"""
    try:
        _iniciar_driver()

        logger.info("[TWITTER] Navegando a X/Twitter...")
        driver.get("https://x.com/compose/post")

        wait = WebDriverWait(driver, 20)

        # Esperar a que cargue el cuadro de texto
        text_box = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]'))
        )

        time.sleep(3)

        # Click via JS para evitar intercepción por overlays
        driver.execute_script("arguments[0].click();", text_box)
        time.sleep(1)

        # Insertar texto simulando un paste (send_keys no soporta emojis)
        driver.execute_script("""
            const el = arguments[1];
            const dt = new DataTransfer();
            dt.setData('text/plain', arguments[0]);
            const paste = new ClipboardEvent('paste', {
                clipboardData: dt,
                bubbles: true,
                cancelable: true
            });
            el.dispatchEvent(paste);
        """, texto, text_box)

        time.sleep(2)

        # Clickear el botón de publicar via JS para evitar intercepción
        post_button = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetButton"]'))
        )
        driver.execute_script("arguments[0].click();", post_button)

        logger.info("[TWITTER] Tweet publicado exitosamente")

        time.sleep(3)
        return True

    except Exception as e:
        logger.error(f"[TWITTER] Error publicando tweet: {e}")
        return False
    finally:
        cerrar_driver()

def cerrar_driver():
    """Cerrar el driver"""
    global driver
    if driver:
        try:
            driver.quit()
            logger.info("[TWITTER] ChromeDriver cerrado")
        except Exception as e:
            logger.error(f"[TWITTER] Error cerrando driver: {e}")
        finally:
            driver = None
