import logging
import os
import redis
import random
import functools

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardRemove
from telegram import ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler
from telegram.ext import Filters, CallbackContext, ConversationHandler
from telegram.ext import RegexHandler

from quiz_tools import load_books, is_answer_right


CHOOSING, ATTEMPT = 1, 2
logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext):
    keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    kb_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(f'Привет ! Я бот для викторин!', reply_markup=kb_markup)
    return CHOOSING


def handle_new_question_request(update: Update, context: CallbackContext, redis_connect, books):
    book_row = random.choice(random.choice(books))
    update.message.reply_text(book_row['question'])
    redis_connect.set(update.message.chat_id, book_row["answer"].encode('koi8-r'))
    return ATTEMPT


def handle_solution_attempt(update: Update, context: CallbackContext, redis_connect):
    user_id = update.message.chat_id
    answer = redis_connect.get(user_id).decode('koi8-r')
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


def handle_right_answer(update, context: CallbackContext, redis_connect):
    answer = redis_connect.get(update.message.chat_id).decode('koi8-r')
    update.message.reply_text(
        f'Правильный ответ: {answer} '
        'Чтобы продолжить нажмите «Новый вопрос».'
    )
    return CHOOSING


def start_bot(token):
    books = load_books()
    redis_connect = redis.Redis(host=os.getenv('REDIS_HOST'), port=os.getenv('REDIS_PORT'), db=0)
    handle_new_question = functools.partial(
        handle_new_question_request,
        redis_connect=redis_connect,
        books=books
    )

    handle_solution = functools.partial(
        handle_solution_attempt,
        redis_connect=redis_connect
    )

    handle_giveup = functools.partial(
        handle_right_answer,
        redis_connect=redis_connect
    )

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [RegexHandler('^Новый вопрос$', handle_new_question)],

            ATTEMPT: [
                RegexHandler('^Сдаться$', handle_giveup),
                MessageHandler(Filters.text, handle_solution)
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
    load_dotenv()
    token = os.getenv('TG_TOKEN')
    start_bot(token)


if __name__ == '__main__':
    main()
