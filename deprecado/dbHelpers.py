
def revisar_conexion(self) -> tuple[bool, str]:
        """
        Verificar si la conexión a la base de datos es válida.
        Retorna (success: bool, message: str)
        """
        try:
            conn = psycopg2.connect(**self.db_config)
            conn.close()
            return True, "Conexión exitosa"
        except psycopg2.OperationalError as e:
            return False, f"Error de conexión: {e}"
        except Exception as e:
            return False, f"Error inesperado: {e}"