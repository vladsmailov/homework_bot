"""Telegram bot for checking homework status."""

import logging
import os

import requests
import time

from telegram import Bot

from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.DEBUG,
    filename='homework.log',
    format='%(asctime)s, %(levelname)s, %(message)s'
)

logger = logging.getLogger(__name__)
handler = RotatingFileHandler(
    'my_logger.log',
    maxBytes=30000000,
    backupCount=5,
    encoding='UTF-8'
)
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


class GetIncorrectAnswer(Exception):
    """Exception for incorrect response."""

    pass


class AbsenceOfRequiredVariables(Exception):
    """Rises in the absence of one of the necessary variables."""

    pass


def send_message(bot, message):
    """Send homework status to your telegram."""
    chat_id = TELEGRAM_CHAT_ID
    bot.send_message(chat_id, message)
    logger.info('Сообщение отправлено успешно', exc_info=True)


def get_api_answer(current_timestamp):
    """Create a request to an api resource."""
    timestamp = current_timestamp or int(time.time())
    URL = ENDPOINT
    params = {'from_date': timestamp}
    response = requests.get(URL, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        raise GetIncorrectAnswer('Проверьте соединение с сервером')


def check_response(response):
    """Check API answer."""
    if not isinstance(response, dict):
        raise TypeError('Результатом запроса должен быть словарь')
    try:
        homework = response.get('homeworks')
    except IndexError:
        logger.error('Неверный индекс', exc_info=True)
    if not isinstance(homework, list):
        logger.error('Неверный формат данных', exc_info=True)
        raise TypeError('Неверный формат данных')
    return homework


def parse_status(homework):
    """Check the homework status."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    try:
        if homework_status is not None:
            verdict = HOMEWORK_STATUSES[homework_status]
    except ValueError:
        logger.debug('Новые данные отсутствуют', exc_info=True)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Check that the parameters are not None."""
    try:
        return (
            (
                PRACTICUM_TOKEN
                and TELEGRAM_TOKEN
                and TELEGRAM_CHAT_ID
            )
        ) is not None
    except AbsenceOfRequiredVariables:
        logger.critical('Отсутствует необходимая переменная', exc_info=True)


def main():
    """Основная логика работы бота."""
    current_timestamp = int(time.time())
    bot = Bot(token=TELEGRAM_TOKEN)
    if check_tokens() is True:
        while True:
            try:
                response = get_api_answer(current_timestamp)
                current_timestamp = response.get('current_date')
                homework = check_response(response)
                message = parse_status(homework[0])
                send_message(bot, message)
                time.sleep(RETRY_TIME)

            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                logger.error('Сбой в работе программы', exc_info=True)
                time.sleep(RETRY_TIME)
    else:
        message = 'Отсутствует один из ключей'
        logger.error('Отсутствует один из ключей', exc_info=True)
        return send_message(bot, message)


if __name__ == '__main__':
    main()
