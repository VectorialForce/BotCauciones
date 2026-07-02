import unittest

from src.database import verificar_conexion


class TestConexionBaseDeDatos(unittest.TestCase):

    def test_verificar_conexion(self):
        """Conexion a PostgreSQL es válida y no lanza excepciones"""
        try:
            verificar_conexion()
        except Exception as e:
            self.fail(f"_verificar_conexion() lanzó una excepción: {e}")

if __name__ == "__main__":
    unittest.main(verbosity=2)