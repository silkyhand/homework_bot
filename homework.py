import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
    filemode='w'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s - %(name)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
SEC_IN_DAY = 86400
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Отправляем сообщение в Telegram чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logger.info(f'Сообщение {message} отправлено в {TELEGRAM_CHAT_ID}')
    except Exception:
        logger.error(f'Сообщение {message} не отправлено в {TELEGRAM_CHAT_ID}')


def get_api_answer(current_timestamp):
    """Запрос к эндпоинту API-сервиса яндекса.
    возвращает ответ API, преобразованный из JSON в Python.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params
        )
    except requests.exceptions.RequestException as error:
        message_api_1 = f'Ошибка при запросе к эндпоинту API: {error}'
        logger.error(message_api_1)
        raise error
    if homework_statuses.status_code != HTTPStatus.OK:
        message_api_2 = (f'Код API:{homework_statuses.status_code},'
                         f'должен быть {HTTPStatus.OK}')
        logger.error(message_api_2)
        raise requests.HTTPError(message_api_2)
    return homework_statuses.json()


def check_response(response):
    """Проверяем ответ API на корректность."""
    if type(response) is not dict:
        message_dict = 'Ответ response не является словарем'
        logger.error(message_dict)
        raise TypeError(message_dict)

    if type(response['homeworks']) is not list:
        message_list = 'Homeworks не является списком'
        logger.error(message_list)
        raise TypeError(message_list)

    if 'homeworks' not in response.keys():
        message_key = 'Отсутствует ключ "homeworks" в словаре response'
        logger.error(message_key)
        raise KeyError(message_key)
    return response.get('homeworks')


def parse_status(homework):
    """Информации о конкретной домашней работе и статус этой работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES.keys():
        message_status = 'Недокументированный статус домашней работы'
        logger.error(message_status)
        raise KeyError(message_status)
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Поверяем доступность переменных окружения."""
    list_of_tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in list_of_tokens:
        if token is None:
            logger.critical(f'Отсутсвует переменная окружения: {token}')
            return False
    return True


def main():
    """Основная логика работы бота."""
    homework_status = ''
    current_timestamp = (int(time.time()) - SEC_IN_DAY)
    error_message = ''
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        while True:
            try:
                response = get_api_answer(current_timestamp)
                check_response_correct = check_response(response)
                if check_response_correct:
                    last_homework = check_response_correct[0]
                    status = parse_status(last_homework)
                    if homework_status != status:
                        homework_status = status
                        send_message(bot, status)
                    else:
                        logger.debug('В ответе нет нового статуса')
                time.sleep(RETRY_TIME)

            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                logger.error(message)
                if error_message != message:
                    send_message(bot, message)
                    error_message = message
                time.sleep(RETRY_TIME)
            else:
                time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
