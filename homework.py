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
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s, %(levelname)s, %(message)s',
    handlers=[
        logging.FileHandler(
            os.path.abspath('program.log'),
            mode='a', encoding='UTF-8'),
        logging.StreamHandler(stream=sys.stdout)],
)
logger = logging.getLogger(__name__)


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens() -> bool:
    """Проверяет  доступность переменных окружения."""
    return all((TELEGRAM_TOKEN, PRACTICUM_TOKEN, TELEGRAM_CHAT_ID))


def send_message(bot: telegram.bot.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение отправлено')
    except telegram.TelegramError as telegram_error:
        logger.error(
            f'Сообщение не отправлено: {telegram_error}')


def get_api_answer(timestamp: int) -> dict:
    """Делает запрос к эндпоинту API-сервиса."""
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params={'from_date': timestamp},
        )
        if homework_statuses.status_code != HTTPStatus.OK:
            raise exceptions.IncorrectResponseCode(
                'Не верный код ответа')
        return homework_statuses.json()
    except exceptions.IncorrectResponseCode as error:
        logger.exception(error)
        raise exceptions.IncorrectResponseCode
    except requests.exceptions.RequestException as request_error:
        logger.exception(request_error)
        raise exceptions.RequestExceptionError


def check_response(response: dict) -> list:
    """Проверяет валидность ответа."""
    try:
        homework = response['homeworks']
    except KeyError as error:
        logging.error(f'Ошибка доступа по ключу homeworks: {error}')
        raise KeyError(f'Ошибка доступа по ключу homeworks: {error}')
    if not isinstance(homework, list):
        logging.error('Homeworks не в виде списка')
        raise TypeError('Homeworks не в виде списка')
    return homework


def parse_status(homework: dict) -> str:
    """Анализирует  статус ответа."""
    if 'homework_name' not in homework:
        raise KeyError('В ответе отсутсвует ключ homework_name')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError(f'Неизвестный статус работы - {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}" {verdict}'


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'Отсутствует токен. Бот остановлен!'
        logging.critical(message)
        sys.exit(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    start_message = 'Бот начал работу'
    send_message(bot, start_message)
    logging.info(start_message)
    prev_msg = ''

    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get(
                'current_date', int(time.time())
            )
            homeworks = check_response(response)
            if homeworks:
                message = parse_status(homeworks[0])
            else:
                message = 'Нет новых статусов'
            if message != prev_msg:
                send_message(bot, message)
                prev_msg = message
            else:
                logging.info(message)
            if message != prev_msg:
                send_message(bot, message)
                prev_msg = message
        except IndexError:
            logging.info('Обновлений не найдено')
        except TypeError as error:
            message = f'Неверный тип данных: {error}'
            logging.error(message)
        except KeyError as error:
            message = f'Ошибка доступа по ключу: {error}'
            logging.error(message)

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
