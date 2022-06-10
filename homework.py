"""Telegram bot for checking homework status."""

import logging
import os
import sys

import requests
import time
from http import HTTPStatus
from json import JSONDecodeError

from telegram import Bot
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

from users_exsceptions import AbsenceOfRequiredVariables, CanNotSendMessage

load_dotenv()

logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler()
handler = RotatingFileHandler(
    "my_logger.log", maxBytes=30000000, backupCount=5, encoding="UTF-8"
)
logger.addHandler(handler)
logger.addHandler(stream_handler)

PRACTICUM_TOKEN = os.getenv("PRACTICUM_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RETRY_TIME = 600
ENDPOINT = "https://practicum.yandex.ru/api/user_api/homework_statuses/"
HEADERS = {"Authorization": f"OAuth {PRACTICUM_TOKEN}"}


HOMEWORK_VERDICTS = {
    "approved": "Работа проверена: ревьюеру всё понравилось. Ура!",
    "reviewing": "Работа взята на проверку ревьюером.",
    "rejected": "Работа проверена: у ревьюера есть замечания.",
}


def send_message(bot, message):
    """Send homework status to your telegram."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info("Сообщение отправлено успешно", exc_info=True)
    except CanNotSendMessage:
        logger.error("Сообщение не отправлено")
        sys.exit(1)


def get_api_answer(current_timestamp):
    """Create a request to an api resource."""
    response_params = dict(
        url=ENDPOINT,
        headers=HEADERS,
        params={"from_date": current_timestamp}
    )
    response = requests.get(**response_params)
    logger.info(
        f"Статус запроса {response.status_code},"
        f" url={response_params['url']},"
        f" params={response_params['params']}"
    )
    if response.status_code != HTTPStatus.OK:
        response.raise_for_status()
    try:
        return response.json()
    except JSONDecodeError:
        raise


def check_response(response):
    """Check API answer."""
    if not isinstance(response, dict):
        raise TypeError("Результатом запроса должен быть словарь")
    try:
        homeworks = response.get('homeworks')
        if 'homeworks' in homeworks and 'current_date' in homeworks:
            if (homeworks['homeworks'] is not None
               and homeworks['current_date'] is not None):
                logger.info('Ключи homeworks и current_date подтверждены',
                            exc_info=True)
            raise ValueError('Данные отсутствуют')
    except KeyError:
        logger.error("Неверный индекс", exc_info=True)
    if not isinstance(homeworks, list):
        raise TypeError("Неверный формат данных")
    return homeworks


def parse_status(homework):
    """Check the homework status."""
    try:
        homework_status = homework.get('status')
        logger.info("Ключ status подтвержден")
        homework_name = homework.get('homework_name')
        logger.info("Ключ homework_name подтвержден")
    except KeyError:
        raise
    try:
        verdict = HOMEWORK_VERDICTS[homework_status]
    except ValueError:
        logger.error("Неизвестный статус", exc_info=True)
        raise
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Check that the parameters are not None."""
    try:
        return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])
    except AbsenceOfRequiredVariables:
        logger.critical("Отсутствует необходимая переменная", exc_info=True)
        raise


def main():
    """Основная логика работы бота."""
    current_timestamp = 0
    bot = Bot(token=TELEGRAM_TOKEN)
    if check_tokens() is False:
        message = "Отсутствует один из ключей"
        logger.critical("Отсутствует один из ключей", exc_info=True)
        sys.exit()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get("current_date")
            homeworks = check_response(response)
            message = parse_status(homeworks[0])
            send_message(bot, message)

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logger.error("Сбой в работе программы", exc_info=True)
            send_message(bot, message)

        finally:
            time.sleep(RETRY_TIME)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        filename=os.path.abspath("homework.log"),
        format="%(asctime)s :: %(levelname)s :: %(message)s",
    )
    main()
