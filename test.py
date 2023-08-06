import logging
import os
import redis
import random
import telebot

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardRemove
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext import Filters, ConversationHandler
from telegram.ext import RegexHandler

from tools import load_book
from tools import is_answer_right
from logger import TelegramLogsHandler

logger = logging.getLogger(__name__)

CHOOSING, ATTEMPT = 1, 2
users_questions = redis.Redis(host='localhost', port=6379, db=0)
BOOKS = []


def start(update: Update):
    keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    kb_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(f'Привет ! Я бот для викторин!', reply_markup=kb_markup)
    return CHOOSING


def help_command(update: Update) -> None:
    update.message.reply_text('Help!')


def handle_new_question_request(update: Update):
    book_row = random.choice(BOOKS[0])
    update.message.reply_text(book_row['question'])
    users_questions.set(f'{update.message.from_user.id}', f'{book_row["answer"]}'.encode('koi8-r'))
    return ATTEMPT


def handle_solution_attempt(update: Update):
    user = update.message.from_user
    answer = users_questions.get(user.id).decode('koi8-r')
    if is_answer_right(answer, update.message.text):
        update.message.reply_text(f'Правильно! Поздравляю! Для следующего вопроса нажмите «Новый вопрос».')
        return CHOOSING
    else:
        update.message.reply_text('Неправильно. Попробуйте ещё раз?')
        return ATTEMPT


def cancel(update: Update):
    update.message.reply_text(
        f'До свидания, {update.message.from_user.first_name}!',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def handle__right_answer(update: Update):
    answer = users_questions.get(update.message.from_user.id).decode('koi8-r')
    update.message.reply_text(
        f'Правильный ответ: {answer} '
        'Чтобы продолжить нажмите «Новый вопрос».'
    )
    return CHOOSING


def processing_errors(bot, update, telegram_error):
    logger.error(f'telegram error: {telegram_error}')


def start_bot(token):

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [RegexHandler('^Новый вопрос$', handle_new_question_request)],

            ATTEMPT: [
                RegexHandler('^Сдаться$', handle__right_answer),
                MessageHandler(Filters.text, handle_solution_attempt)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(conversation_handler)
    dispatcher.add_error_handler(processing_errors)
    updater.start_polling()
    updater.idle()


def main() -> None:
    BOOKS.append(load_book())
    load_dotenv()
    token = os.getenv('TG_TOKEN')
    chat_log_id = os.environ['TG_CHAT_ID']
    bot = telebot.TeleBot(token)
    telegram_handler = TelegramLogsHandler(bot, chat_log_id)
    telegram_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(telegram_handler)
    logging.basicConfig(level=logging.ERROR)
    logger.setLevel(logging.DEBUG)
    logger.info('The dialogflow bot started!')

    start_bot(token)


if __name__ == '__main__':
    main()
