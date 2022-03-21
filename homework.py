import logging
import os
import time
import sys

import json
import requests
import telegram
from dotenv import load_dotenv
from http import HTTPStatus

import exceptions


load_dotenv()


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


logging.basicConfig(handlers=[logging.FileHandler(
    filename='program.log',
    encoding='utf-8',
    mode='a+'
)],
    level=logging.DEBUG,
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='my_logger.log',
    encoding='utf-8',
    mode='w'
)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправка сообщения ботом в чат."""
    logger.info(f'Отправка {message}')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.error.TelegramError as error:
        logger.error(f'Возникла ошибка Телеграм: {error.message}')
        raise telegram.error.TelegramError(f'Ошибка при отправке: {message}')
    except json.decoder.JSONDecodeError:
        raise telegram.error.TelegramError(
            f'Ошибка разбора ответа при отправке: {message}'
        )


def get_api_answer(current_timestamp):
    """делает запрос к серверу."""
    timestamp = current_timestamp or int(time.time())
    params = {"from_date": timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        error = "Бот не получил ответ API."
        logging.error(error)
    if response != HTTPStatus.OK:
        raise exceptions.ServerError(exceptions.SERVER_PROBLEMS)
    return response.json()


def check_response(response: list):
    """Валидация ответов API."""
    if 'error' in response:
        raise exceptions.ResponseError(exceptions.RESPONSE_ERROR)
    if 'homeworks' not in response:
        raise exceptions.HomeworkKeyError(exceptions.HOMEWORK_KEY_ERROR)
    if not isinstance(response['homeworks'], list):
        raise exceptions.HomeworkListError(exceptions.HOMEWORK_LIST_ERROR)
    return response['homeworks']

#я разделил на два метода,
# по тому что не очень понимаю как прописать в одном
def check_response_status(homework: dict):
    """Дополнительная валидация ответов API."""
    if not isinstance(homework, dict):
        raise exceptions.HomeworkDictError(exceptions.HOMEWORK_DICT_ERROR)
    status = homework.get("status")
    if status not in HOMEWORK_STATUSES:
        raise KeyError(exceptions.PARSE_STATUS_ERROR)
    return True


def parse_status(homework: dict):
    """Извлекает статус запрошенной работы."""
    check_response_status(homework)
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(f'Неизвестный статус {homework_status}')
    verdict = HOMEWORK_STATUSES.get(homework_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка сетевого окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    logger.debug('Запуск бота')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    check_previous_error = ""
    while True:
        try:
            current_timestamp = int(time.time())
            api_answer = get_api_answer(current_timestamp)
            current_timestamp = api_answer.get(
                'current_date')
            result = check_response(api_answer)
            if result:
                print('Задания обнаружены')
            else:
                print('Задания не обнаружены')
            for homework in result:
                parse_status_result = parse_status(homework[0])
                send_message(bot, parse_status_result)
            check_previous_error = ""
        except Exception as error:
            message = f'Бот столкнулся с ошибкой: {error}'
            logger.exception(message)
            if check_previous_error != error:
                check_previous_error = error
        time.sleep(RETRY_TIME)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Выход из программы')
        sys.exit(0)
