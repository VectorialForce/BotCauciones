from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium_stealth import stealth
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from os import getenv
from pathlib import Path
import logging
import time
from src.config import configurar_logging
from src.bot import get_tasas_caucion

logger = configurar_logging()

chrome_profile_path = chrome_profile_path or getenv("CHROME_PROFILE_PATH", "chrome_profile")
driver = None

def _iniciar_driver() -> bool:
        """Inicializar ChromeDriver con stealth"""
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
        try: 
            profile_abs = str(Path(chrome_profile_path).resolve())
            options.add_argument(f"--user-data-dir={profile_abs}")
        except Exception as e:
            logging.info(e)
            logging.info("No importaste una sesion abierta de twitter")
            return False


        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        driver = webdriver.Chrome(options=options, service=service) if service else webdriver.Chrome(options=options)

        stealth(
            self.driver,
            languages=["es-AR", "es"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
        )

        logger.info("[TWITTER] ChromeDriver inicializado con stealth")

def tweet(texto: str) -> bool:
    """Publicar tweet"""
    try:
        _iniciar_driver()

        logger.info("[TWITTER] Navegando a X/Twitter...")
        driver.get("https://x.com/compose/post")

        wait = WebDriverWait(self.driver, 20)

        # Esperar a que cargue el cuadro de texto
        text_box = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetTextarea_0"]'))
        )

        time.sleep(3)

        # Click via JS para evitar intercepción por overlays
        self.driver.execute_script("arguments[0].click();", text_box)
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
            self.driver.execute_script("arguments[0].click();", post_button)

            logger.info("[TWITTER] Tweet publicado exitosamente")

            time.sleep(3)
            return True

        except Exception as e:
            logger.error(f"[TWITTER] Error publicando tweet: {e}")
            return False
        finally:
            self.close()
