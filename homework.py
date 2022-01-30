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
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
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

bot = telegram.Bot(token=TELEGRAM_TOKEN)

message_not_api = 0

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
    global message_not_api  
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
        message_not_api  = 0
    except requests.exceptions.RequestException as error:        
        message = f'Ошибка при запросе к эндпоинту API: {error}'
        logger.error(message)
        if message_not_api == 0:
            message_not_api = 1
            send_message(bot, message)                     
    return homework_statuses.json()


def check_response(response):
    """Проверяем ответ API на корректность"""
    if type(response) is not dict:
        message_dict = 'Ответ response не является словарем'
        logger.error(message_dict)
        send_message(bot, message_dict) 
        raise TypeError(message_dict)
        
    if 'homeworks' not in response.keys():
        message_key = 'Отсутствует ключ "homeworks" в словаре response'
        logger.error(message_key)
        send_message(bot, message_key) 
        raise KeyError(message_key)
    return response.get('homeworks') 


def parse_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES.keys():
        message_status = 'Недокументированный статус домашней работы'
        logger.error(message_status)
        send_message(bot, message_status)  
        raise KeyError(message_status)  
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """ Поверяем доступность переменных окружения."""
    list_of_tokens = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in list_of_tokens:
        if token is None:
            logger.critical(f'Отсутсвует переменная окружения: {token}')
            return False
        return True    



def main():
    """Основная логика работы бота."""
    homework_status = ''     
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            check_response_correct = check_response(response)
            if check_response_correct:
                last_homework =check_response_correct[0]
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
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    if check_tokens:
        main()


