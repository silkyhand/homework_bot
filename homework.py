import time
import os
import requests
import telegram
import sys
import logging
from logging.handlers import StreamHandler


from dotenv import load_dotenv
from telegram import Bot
load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log', 
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
    filemode='w'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s - %(name)s - %(funcName)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """ Отправляем сообщение в Telegram чат"""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(f'Сообщение {message} отправлено в {TELEGRAM_CHAT_ID}')
    except Exception:
        logger.error(f'Сообщение {message} не отправлено в {TELEGRAM_CHAT_ID}')



def get_api_answer(current_timestamp):
    """Запрос к эндпоинту API-сервиса яндекса.    
    возвращает ответ API, преобразованный из JSON в Python
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        logging.error(f'Ошибка при запросе к основному API: {error}')
        raise Exception(f'Ошибка при запросе к основному API: {error}')    
    


def check_response(response):

    ...


def parse_status(homework):
    homework_name = ...
    homework_status = ...

    ...

    verdict = ...

    ...

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    ...


def main():
    """Основная логика работы бота."""    
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())


    while True:
        try:
            response = ...

            ...

            current_timestamp = ...
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            ...
            time.sleep(RETRY_TIME)
        else:
            ...


if __name__ == '__main__':
    main()


PRACTICUM_TOKEN=AQAAAAAFw6l_AAYckc9oWTO7oEgiuzim9vFUT6g
TELEGRAM_TOKEN=5151322602:AAG3x24OJmksAwz0zuAgXJUbctjSE_m-HT0
TELEGRAM_CHAT_ID=5196380385