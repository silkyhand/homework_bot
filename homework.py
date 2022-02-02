from json import JSONDecodeError
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


VERDICTS = {
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
        logger.exception(f'Сообщение {message}'
                         f' не отправлено в {TELEGRAM_CHAT_ID}')


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
        print(type(homework_statuses))
    except requests.exceptions.RequestException as error:
        api_request_error = f'Ошибка при запросе к эндпоинту API: {error}'
        logger.error(api_request_error)
        raise error
    if homework_statuses.status_code != HTTPStatus.OK:
        api_status_error = (f'Код API:{homework_statuses.status_code},'
                            f'должен быть {HTTPStatus.OK}')
        logger.error(api_status_error)
        raise requests.HTTPError(api_status_error)
    try:
        homework_statuses.json()
    except JSONDecodeError:
        api_json_error = 'Некорректный json'
        logger.error(api_json_error)
        raise JSONDecodeError(api_json_error)
    return homework_statuses.json()


def check_response(response):
    """Проверяем ответ API на корректность."""
    if not isinstance(response, dict):
        message_dict = 'Ответ response не является словарем'
        logger.error(message_dict)
        raise TypeError(message_dict)

    if 'homeworks' not in response.keys():
        message_key = 'Отсутствует ключ "homeworks" в словаре response'
        logger.error(message_key)
        raise KeyError(message_key)

    if not isinstance((response['homeworks']), list):
        message_list = 'homeworks не является списком'
        logger.error(message_list)
        raise TypeError(message_list)

    return response.get('homeworks')


def parse_status(homework):
    """Информации о конкретной домашней работе и статус этой работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is None:
        message_not_name = 'Отсутствует параметр "homework_name"'
        logger.error(message_not_name)
        raise KeyError(message_not_name)

    if homework_status is None:
        message_not_status = 'Отсутствует параметр "homework_status"'
        logger.error(message_not_status)
        raise KeyError(message_not_status)

    if homework_status not in VERDICTS.keys():
        message_status = 'Недокументированный статус домашней работы'
        logger.error(message_status)
        raise KeyError(message_status)
    verdict = VERDICTS[homework_status]
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
    if not check_tokens():
        return
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    while True:
        try:
            response = get_api_answer(current_timestamp)
            check_response_correct = check_response(response)
            if check_response_correct:
                last_homework = check_response_correct[0]
                status = parse_status(last_homework)
                print(status)
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


if __name__ == '__main__':
    main()
