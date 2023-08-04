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

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

CHOOSING, ATTEMPT = 1, 2
logger = logging.getLogger(__name__)
users_questions = redis.Redis(host='localhost', port=6379, db=0)
BOOKS = []


def is_answer_right(answer, message):
    point_index = answer.find('.')
    if point_index >= 0:
        answer = answer[0:answer.find('.')]
    point_index = message.find('.')
    if point_index >= 0:
        message = message[0:message.find('.')]
    return answer.strip().lower() == message.strip().lower()


def load_book(file_name='questions/1vs1200.txt') -> list:
    book = []
    with open(file_name, "rb") as file:
        data = file.read().decode('koi8-r')
    is_it_question = False;
    is_it_answer = False;
    question, answer = '', ''
    for line in data.splitlines():
        if not line:
            is_it_answer = False
            is_it_question = False
        if is_it_question:
            question += f'{line.strip()}\n'
        if is_it_answer:
            answer += f'{line.strip()}\n'
        if line.find('Вопрос') >= 0:
            if question:
                book.append({'question': question, 'answer': answer})
            question = ''
            is_it_question = True
            is_it_answer = False
            continue
        if line.find('Ответ') >= 0:
            answer = ''
            is_it_question = False
            is_it_answer = True
            continue
    return book


def start(update: Update, context: CallbackContext) -> None:
    keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    kb_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    update.message.reply_text(f'Привет ! Я бот для викторин!', reply_markup=kb_markup)
    return CHOOSING


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Help!')


def handle_new_question_request(update: Update, context: CallbackContext):
    book_row = random.choice(BOOKS[0])
    update.message.reply_text(book_row['question'])
    users_questions.set(f'{update.message.from_user.id}', f'{book_row["answer"]}'.encode('koi8-r'))
    return ATTEMPT


def handle_solution_attempt(update: Update, context: CallbackContext):
    user = update.message.from_user
    answer = users_questions.get(user.id).decode('koi8-r')
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
    answer = users_questions.get(update.message.from_user.id).decode('koi8-r')
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


def main() -> None:
    BOOKS.append(load_book())
    load_dotenv()
    token = os.getenv('TG_TOKEN')
    start_bot(token)


if __name__ == '__main__':
    main()
