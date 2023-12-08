"""
Configure logger: 
https://docs.python.org/3/howto/logging.html#configuring-logging
"""
import logging
from logging.handlers import RotatingFileHandler
from telegram_handler.handlers import TelegramHandler
from telegram_handler.formatters import HtmlFormatter

log = logging.getLogger('main')

def init_logger(filename, telegram_bot_token, telegram_chat_id, telegram_message_thread_id):

    log.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(levelname)s: %(message)s')

    stream_handler.setFormatter(formatter)

    log.addHandler(stream_handler)

    file_handler = RotatingFileHandler(filename, mode='a', maxBytes=1024*1024*10, backupCount=3, encoding="utf8")
    file_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(levelname)s\t: %(asctime)s - %(message)s')
    file_handler.setFormatter(formatter)

    log.addHandler(file_handler)
    telegram_handler = TelegramHandler(level=logging.WARNING, token=telegram_bot_token, chat_id=telegram_chat_id, message_thread_id=telegram_message_thread_id)
    telegram_handler.setLevel(logging.WARNING)

    formatter = HtmlFormatter()
    telegram_handler.setFormatter(formatter)

    log.addHandler(telegram_handler)