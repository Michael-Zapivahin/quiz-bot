import logging
import os
import redis
import random

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardRemove
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext import Filters, CallbackContext, ConversationHandler
from telegram.ext import RegexHandler

from bots_tools import load_book, is_answer_right

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

CHOOSING, ATTEMPT = 1, 2
logger = logging.getLogger(__name__)
users_right_answers = redis.Redis(host='localhost', port=6379, db=0)
BOOKS = []


def start(update: Update, context: CallbackContext):
    keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    kb_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(f'Привет ! Я бот для викторин!', reply_markup=kb_markup)
    return CHOOSING


def help_command(update: Update, context: CallbackContext):
    update.message.reply_text('Help!')


def handle_new_question_request(update: Update, context: CallbackContext):
    book_row = random.choice(BOOKS[0])
    update.message.reply_text(book_row['question'])
    users_right_answers.set(f'{update.message.from_user.id}', f'{book_row["answer"]}'.encode('koi8-r'))
    return ATTEMPT


def handle_solution_attempt(update: Update, context: CallbackContext):
    user = update.message.from_user
    answer = users_right_answers.get(user.id).decode('koi8-r')
    if is_answer_right(answer, update.message.text):
        update.message.reply_text(f'Правильно! Поздравляю! Для следующего вопроса нажмите «Новый вопрос».')
        return CHOOSING
    else:
        update.message.reply_text('Неправильно. Попробуйте ещё раз?')
        return ATTEMPT


def cancel(update: Update, context: CallbackContext):
    update.message.reply_text(
        f'До свидания, {update.message.from_user.first_name}!',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def handle__right_answer(update: Update, context: CallbackContext):
    answer = users_right_answers.get(update.message.from_user.id).decode('koi8-r')
    update.message.reply_text(
        f'Правильный ответ: {answer} '
        'Чтобы продолжить нажмите «Новый вопрос».'
    )
    return CHOOSING


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
    updater.start_polling()
    updater.idle()


def main():
    BOOKS.append(load_book())
    load_dotenv()
    token = os.getenv('TG_TOKEN')
    start_bot(token)


if __name__ == '__main__':
    main()
