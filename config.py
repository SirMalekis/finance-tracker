import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Загружаем переменную ключа из .env
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    # Секретный ключ
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Подключение к БД (передача через docker-compose)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    SQLALCHEMY_TRACK_MODIFICATIONS = False