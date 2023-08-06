
def is_answer_right(answer, message):
    point_index = answer.find('.')
    if point_index >= 0:
        answer = answer[0:answer.find('.')]
    point_index = message.find('.')
    if point_index >= 0:
        message = message[0:message.find('.')]
    return answer.strip().lower() == message.strip().lower()


def load_book(file_name='questions/1vs1200.txt'):
    book = []
    with open(file_name, "rb") as file:
        data = file.read().decode('koi8-r')
    is_it_question = False
    is_it_answer = False
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
