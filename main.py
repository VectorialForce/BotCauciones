# Desde main unicamente lo que se debe hacer es apuntar a prod o a test
from src.bot import conectar_ppi
from src.bot import get_tasas_caucion
from src.database import guardar_tasas

def main():
    conectar_ppi()
    
    tasas = get_tasas_caucion()
    guardar_tasas(tasas)
    
    print(tasas)

if __name__ == '__main__':
    main()