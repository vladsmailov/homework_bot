"""Telegram bot for checking homework status."""

import logging
import os
import sys

import requests
import time
from http import HTTPStatus
from json import JSONDecodeError

from telegram import Bot, TelegramError
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

from users_exsceptions import NotForSend

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
    except TelegramError:
        logger.error("Сообщение не отправлено", exc_info=True)
    else:
        logger.info("Сообщение отправлено успешно")


def get_api_answer(current_timestamp):
    """Create a request to an api resource."""
    response_params = dict(
        url=ENDPOINT,
        headers=HEADERS,
        params={"from_date": current_timestamp}
    )
    try:
        response = requests.get(**response_params)
        if response.status_code != HTTPStatus.OK:
            raise NotForSend
        return response.json()
    except requests.RequestException:
        raise
    except JSONDecodeError:
        raise


def check_response(response):
    """Check API answer."""
    if not isinstance(response, dict):
        raise TypeError("Результатом запроса должен быть словарь")
    homeworks = response.get('homeworks')
    if homeworks is None or 'current_date' not in response:
        raise NotForSend
    if not isinstance(homeworks, list):
        raise TypeError("Неверный формат данных")
    return homeworks


def parse_status(homework):
    """Check the homework status."""
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    if homework_name is None and homework_status is None:
        raise NotForSend
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    if verdict is None:
        raise KeyError
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Check that the parameters are not None."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if check_tokens() is not True:
        message = "Отсутствует один из ключей"
        logger.critical("Отсутствует один из ключей", exc_info=True)
        sys.exit(1)
    current_timestamp = 0
    while True:
        bot = Bot(token=TELEGRAM_TOKEN)
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get("current_date")
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
            else:
                message = 'Список домашних работ пуст'
            send_message(bot, message)
        except NotForSend:
            logger.error("Сбой в работе программы", exc_info=True)
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
