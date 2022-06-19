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

from users_exceptions import NotForSend, GetIncorrectAnswer

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
    except TelegramError as e:
        raise NotForSend(message) from e
    else:
        logger.info("Сообщение отправлено успешно")


def get_api_answer(current_timestamp):
    """Create a request to an api resource."""
    requests_params = dict(
        url=ENDPOINT,
        params={"from_date": current_timestamp}
    )
    try:
        response = requests.get(headers=HEADERS, **requests_params)
    except requests.exceptions.RequestException as e:
        raise GetIncorrectAnswer(requests_params) from e

    if response.status_code != HTTPStatus.OK:
        raise GetIncorrectAnswer(
            'Несоответствующий код ответа',
            requests_params,
            response.status_code
        )
    try:
        return response.json()
    except JSONDecodeError as e:
        raise GetIncorrectAnswer(
            'Несоответствующий формат данных',
            requests_params,
            response.status_code
        ) from e


def check_response(response):
    """Check API answer."""
    if not isinstance(response, dict):
        raise TypeError("Результатом запроса должен быть словарь")
    homeworks = response.get('homeworks')
    if homeworks is None:
        raise KeyError("Отсутствуют данные по домашним работам")
    if 'current_date' not in response:
        raise NotForSend("Отсутствует ключ current_date")
    if not isinstance(homeworks, list):
        raise TypeError("Несоответствующий формат данных запроса")
    return homeworks


def parse_status(homework):
    """Check the homework status."""
    homework_status = homework.get('status')
    homework_name = homework.get('homework_name')
    if homework_name is None:
        raise KeyError("Отсутствуют данные по запросу")
    verdict = HOMEWORK_VERDICTS.get(homework_status)
    if verdict is None:
        raise KeyError("Неизвестный статус")
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Check that the parameters are not None."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = "Отсутствует один из ключей"
        logger.critical("Отсутствует один из ключей", exc_info=True)
        sys.exit(1)
    current_timestamp = int(time.time())
    while True:
        bot = Bot(token=TELEGRAM_TOKEN)
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            current_timestamp = response.get("current_date")
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
