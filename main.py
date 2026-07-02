# Desde main unicamente lo que se debe hacer es apuntar a prod o a test
from src import bot
from src import database
from src import telegram


def main():
    ultimas_tasas = bot.get_tasas_caucion()
    if ultimas_tasas:
        database.set_tasas(ultimas_tasas)

    telegram.activar_caucho_bot()


if __name__ == '__main__':
    main()
