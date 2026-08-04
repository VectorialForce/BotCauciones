import unittest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.database import verificar_conexion
from src import twitter


class TestConexionBaseDeDatos(unittest.TestCase):

    def test_verificar_conexion(self):
        """Conexion a PostgreSQL es válida y no lanza excepciones"""
        try:
            verificar_conexion()
        except Exception as e:
            self.fail(f"_verificar_conexion() lanzó una excepción: {e}")


class TestModuloTwitter(unittest.TestCase):

    def test_sesion_abierta(self):
        """La sesión de Twitter/X en el perfil de Chrome sigue activa"""
        try:
            twitter._iniciar_driver()
            twitter.driver.get("https://x.com/home")

            WebDriverWait(twitter.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="SideNav_NewTweet_Button"]'))
            )

            self.assertNotIn("/login", twitter.driver.current_url, "Redirigido a login: la sesión no está activa")
        except Exception as e:
            self.fail(f"La sesión de Twitter no está activa: {e}")
        finally:
            twitter.cerrar_driver()

    def test_puede_tuitear(self):
        """El módulo puede publicar un tweet de prueba"""
        resultado = twitter.tuitear("test")
        self.assertTrue(resultado, "twitter.tuitear() no pudo publicar el tweet de prueba")


if __name__ == "__main__":
    unittest.main(verbosity=2)