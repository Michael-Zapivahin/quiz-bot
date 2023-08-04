import logging
import os
import telegram
import redis
import functools

from dotenv import load_dotenv
from telegram import Update, ForceReply, ReplyKeyboardRemove
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
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    update.message.reply_text(f'Привет ! Я бот для викторин!', reply_markup=reply_markup)


def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Help!')


def echo(update: Update, context: CallbackContext) -> None:
    custom_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    user = update.effective_user
    answer = users_questions.get(user.id).decode('koi8-r')
    if is_answer_right(answer, update.message.text):
        update.message.reply_text(f'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос».', reply_markup=reply_markup)
    else:
        update.message.reply_text('Неправильно… Попробуешь ещё раз?', reply_markup=reply_markup)
    if update.message.text =='Новый вопрос':
        update.message.reply_text(BOOKS[0][0]['question'])
        users_questions.set(f'{user.id}', f'{BOOKS[0][0]["answer"]}'.encode('koi8-r'))


def send_new_question(bot, update, redis_conn):

    question = users_questions.get('question')
    update.message.reply_text(question)

    return ATTEMPT


def processing_response(bot, update, redis_conn):
    user_id = update.message.from_user.id
    return ATTEMPT


def cancel(bot, update):
    update.message.reply_text(
        f'До свидания, {update.message.from_user.first_name}!',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def send_right_answer(bot, update, redis_conn):
    user_id = update.message.from_user.id
    answer = ''
    update.message.reply_text(
        f'Вот тебе правильный ответ: {answer} '
        'Чтобы продолжить нажми «Новый вопрос»'
    )

    return CHOOSING


def start_bot(token):
    BOOKS.append(load_book())

    updater = Updater(token)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))

    handle_new_question = functools.partial(
        send_new_question,
        redis_conn=users_questions
    )

    handle_answer = functools.partial(
        processing_response,
        redis_conn=users_questions
    )

    handle_right_answer = functools.partial(
        send_right_answer,
        redis_conn=users_questions
    )

    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOOSING: [RegexHandler('^Новый вопрос$', handle_new_question)],

            ATTEMPT: [
                RegexHandler('^Сдаться$', handle_right_answer),
                MessageHandler(Filters.text, handle_answer)
            ]
        },

        fallbacks=[CommandHandler('cancel', cancel)]

    )

    dispatcher.add_handler(conversation_handler)
    updater.start_polling()
    updater.idle()


def main() -> None:
    load_dotenv()
    token = os.getenv('TG_TOKEN')
    updater = Updater(token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
