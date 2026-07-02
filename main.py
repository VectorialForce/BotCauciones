# Desde main unicamente lo que se debe hacer es apuntar a prod o a test
from src import bot


def main():

    '''
    Comportamiento esperado del main

    Precondiciones:
    - una flag general dentro del main para apuntar a prod o test

    1. llamar a la api de ppi para obtener las tasas
    2. guardar las mismas en la base de datos
    3. activar bot telegram
    4. activar bot twitter
    '''
    
    ultimas_tasas = bot.get_tasas_caucion()
    print(ultimas_tasas)
    #database.set_tasas(ultimas_tasas)

    #bot.activar_caucho_bot()

if __name__ == '__main__':
    main()