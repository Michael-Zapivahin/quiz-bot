
def load_books():
    book = []
    with open('questions/1vs1200.txt', "rb") as file:
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
    print(book)


if __name__ == '__main__':
    load_books()


