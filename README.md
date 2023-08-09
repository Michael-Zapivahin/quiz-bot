## The Bot "Quiz"

### This repository contains bots for quizzes in "Telegram" and "VK"

### https://github.com/Michael-Zapivahin/quiz-bot
 
## How install:

Python3 should already be installed. 
Use pip or pip3, if there is a conflict with Python2) to install dependencies:

It is recommended to install dependencies in a virtual environment [virtualenv](https://github.com/pypa/virtualenv), [virtualenvwrapper](https://pypi.python.org/pypi/virtualenvwrapper) 
or [venv](https://docs.python.org/3/library/venv.html).

1. Copy repository to bots' catalog:
```bash
$ git clone https://github.com/Michael-Zapivahin/quiz-bot
```

2. Create and activate a virtual environment:
```bash
$ cd quiz-bot# Переходим в каталог с программой
$ python3 -m venv example_environment 
$ source example_environment/bin/activate 
```
2. Install external libraries
```
pip install -r requirements.txt
```

## Program uses an environment variable

#### Variables:

```  
TG_TOKEN: telegram bot token
VK_TOKEN: VK goup token
QUESTIONS_FOLDER: the path to the folder with the question files
```  
# Start

```python
python tgbot.py # Telegram-bot
python vkbot.py # VK - bot
```

## The aim of the project 
The code is written for educational purposes on the online course for web developers [Devman практика Python](https://dvmn.org/)