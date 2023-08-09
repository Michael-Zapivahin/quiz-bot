
import os
import re

from dotenv import load_dotenv


def is_answer_right(answer, message):
    point_index = answer.find('.')
    if point_index >= 0:
        answer = answer[0:answer.find('.')]
    point_index = message.find('.')
    if point_index >= 0:
        message = message[0:message.find('.')]
    return answer.strip().lower() == message.strip().lower()


def load_books():
    load_dotenv()
    questions_folder = os.getenv('QUESTIONS_FOLDER', default='questions')
    books = []
    for file_name in os.listdir(questions_folder):
        book = []
        with open(os.path.join(questions_folder, file_name), 'rb') as file:
            data = file.read().decode('koi8-r')
        lines = data.split('\n\n\n')
        for line in lines:
            question_and_answer = line.split('\n\n')
            question_text, answer_text = '', ''
            for text in question_and_answer:
                if re.findall('Вопрос.*:', text):
                    question_text = re.split('Вопрос.*:', text)[1]
                    question_text = question_text.replace('\n', ' ')
                if re.findall('Ответ:', text):
                    answer_text = re.split('Ответ:', text)[1]
                    answer_text = answer_text.replace('\n', ' ')
            if question_text and answer_text:
                book.append({'question': question_text, 'answer': answer_text})
        books.append(book)
    return books


