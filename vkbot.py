import logging
import os
import random
import sys

import redis
import vk_api

from dotenv import load_dotenv
from vk_api.keyboard import VkKeyboard
from vk_api.keyboard import VkKeyboardColor
from vk_api.longpoll import VkEventType
from vk_api.longpoll import VkLongPoll
from vk_api.utils import get_random_id

from bots_tools import is_answer_right, load_book


logger = logging.getLogger(__name__)
users_right_answers = redis.Redis(host='localhost', port=6379, db=0)
BOOKS = []


def get_custom_keyboard():
    keyboard = VkKeyboard()
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()


def handle_new_question(event, vk):
    book_row = random.choice(BOOKS[0])
    users_right_answers.set(f'{event.user_id}', f'{book_row["answer"]}'.encode('koi8-r'))
    vk.messages.send(
        peer_id=event.user_id,
        random_id=get_random_id(),
        keyboard=get_custom_keyboard(),
        message=book_row['question']
    )


def handle_solution_attempt(event, vk):
    answer = users_right_answers.get(event.user_id).decode('koi8-r')
    if is_answer_right(answer, event.text):
        vk.messages.send(
            peer_id=event.user_id,
            random_id=get_random_id(),
            keyboard=get_custom_keyboard(),
            message=f'Правильно! Поздравляю! Для следующего вопроса нажмите «Новый вопрос».'
        )
    else:
        vk.messages.send(
            peer_id=event.user_id,
            random_id=get_random_id(),
            keyboard=get_custom_keyboard(),
            message='Неправильно. Попробуйте ещё раз.'
        )


def handle_give_up(event, vk):
    answer = users_right_answers.get(event.user_id).decode('koi8-r')
    response = (
        f'Правильный ответ: {answer} '
        'Чтобы продолжить нажмите «Новый вопрос».'
    )
    vk.messages.send(
        peer_id=event.user_id,
        random_id=get_random_id(),
        keyboard=get_custom_keyboard(),
        message=response
    )


def start_bot(vk_session):
    api_vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    for event in longpoll.listen():
        if not (event.type == VkEventType.MESSAGE_NEW and event.to_me):
            continue

        if event.text == 'Новый вопрос':
            handle_new_question(event, api_vk)
            continue

        if event.text == 'Сдаться':
            handle_give_up(event, api_vk)
            continue

        handle_solution_attempt(event, api_vk)


def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    load_dotenv()
    vk_token = os.getenv('VK_TOKEN')
    vk_session = vk_api.VkApi(token=vk_token)
    BOOKS.append(load_book())
    while True:
        try:
            start_bot(vk_session)
        except Exception as err:
            logger.error(f'Бот "{__file__}" упал с ошибкой.')
            logger.exception(err)
            continue


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
