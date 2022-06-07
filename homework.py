"""Telegram bot for checking homework status."""

import logging
import os
import sys

import requests
import time
from http import HTTPStatus

from telegram import Bot
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

from users_exsceptions import AbsenceOfRequiredVariables

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
    bot.send_message(TELEGRAM_CHAT_ID, message)
    logger.info("Сообщение отправлено успешно", exc_info=True)


def get_api_answer(current_timestamp):
    """Create a request to an api resource."""
    timestamp = current_timestamp
    params = {"from_date": timestamp}
    response = requests.get(url=ENDPOINT, headers=HEADERS, params=params)
    logger.info(f"Статус запроса {response.status_code}, params = {params}")
    try:
        if response.status_code == HTTPStatus.OK:
            return response.json()
        raise requests.JSONDecodeError
    except Exception:
        response.raise_for_status()


def check_response(response):
    """Check API answer."""
    if not isinstance(response, dict):
        raise TypeError("Результатом запроса должен быть словарь")
    try:
        homeworks = response.get('homeworks', 'current_date')
        if ('homeworks' and 'current_date') in homeworks:
            if (homeworks['homeworks']
               and homeworks['current_date']) is not None:
                logger.info('Ключи homeworks и current_date подтверждены',
                            exc_info=True)
                return homeworks
            raise ValueError('Данные отсутствуют')
    except KeyError:
        logger.error("Неверный индекс", exc_info=True)
    if not isinstance(homeworks, list):
        logger.error("Неверный формат данных", exc_info=True)
        raise TypeError("Неверный формат данных")
    return homeworks


def parse_status(homeworks):
    """Check the homework status."""
    try:
        "homework_name" in homeworks == True
        homework_name = homeworks["homework_name"]
        logger.info("Ключ homework_name подтвержден")
    except KeyError:
        logger.error("Ключ homework_name отсутствует")
    try:
        "status" in homeworks == True
        homework_status = homeworks["status"]
        logger.info("Ключ status подтвержден")
    except KeyError:
        logger.error("Ключ status отсутствует")
    try:
        if homework_status in HOMEWORK_VERDICTS:
            verdict = HOMEWORK_VERDICTS[homework_status]
    except ValueError:
        logger.error("Неизвестный статус", exc_info=True)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Check that the parameters are not None."""
    try:
        return (PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID)
    except AbsenceOfRequiredVariables:
        logger.critical("Отсутствует необходимая переменная", exc_info=True)


def main():
    """Основная логика работы бота."""
    current_timestamp = 0
    bot = Bot(token=TELEGRAM_TOKEN)
    if check_tokens() is False:
        sys.exit()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get("current_date")
            homeworks = check_response(response)
            message = parse_status(homeworks[0])
            send_message(bot, message)
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f"Сбой в работе программы: {error}"
            logger.error("Сбой в работе программы", exc_info=True)
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            message = "Отсутствует один из ключей"
            logger.critical("Отсутствует один из ключей", exc_info=True)
            sys.exit(1)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        filename=os.path.abspath("homework.log"),
        format="%(asctime)s :: %(levelname)s :: %(message)s",
    )
    main()
