import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

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


logger = logging.getLogger(__name__)
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s, %(levelname)s, %(message)s, %(name)s",
)
logger.addHandler(logging.StreamHandler())


def send_message(bot, message):
    """Отправка сообщения ботом в чат."""
    logger.info(f'Отправка {message}')
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.error.TelegramError as error:
        logger.error(f'Возникла ошибка Телеграм: {error.message}')
        raise telegram.error.TelegramError(f'Ошибка при отправке: {message}')


def get_api_answer(current_timestamp):
    """делает запрос к серверу."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        logger.info(
            f'Отправлен запрос к API Яндекс.Домашки с параметрами: {params}'
        )
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise exceptions.ResponseError('Код ответа отличается от 200')
        return response.json()
    except Exception as error:
        logger.error(f'Ошибка при запросе {error}')
        raise exceptions.ResponseError(
            f'Ошибка при запросе к API Яндекс.Домашка: {error}'
        ) 


def check_response(response):
    """Валидация ответов API."""
    try:
        homework = response["homeworks"]
    except KeyError as error:
        logger.error(f"Отсутствие ожидаемых ключей в ответе API: {error}")
        raise KeyError("Отсутствие ожидаемых ключей в ответе API:")
    if not isinstance(response["homeworks"], list):
        raise TypeError("Неверный тип ответа API")
    return homework


def parse_status(homework: dict):
    """Извлекает статус запрошенной работы."""
    if ("homework_name") not in homework:
        raise KeyError("Отсутствует ключ homework_name в ответе API")
    if ("status") not in homework:
        raise KeyError("Отсутствует ключ status в ответе API")
    homework_name = homework.get("homework_name")
    homework_status = homework.get("status")
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError("Такого статуса нет")
    else:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка сетевого окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    logger.debug('Запуск бота')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

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
        except Exception as error:
            message = f'Бот столкнулся с ошибкой: {error}'
            logger.exception(message)
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Выход из программы')
        sys.exit(0)
