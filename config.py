import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Загружаем переменные из .env, если он существует (для локальной разработки)
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    # Секретный ключ берем из переменных окружения
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Строка подключения к БД. Она будет передана через docker-compose
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    SQLALCHEMY_TRACK_MODIFICATIONS = False