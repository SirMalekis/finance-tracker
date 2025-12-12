FROM python:3.9-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PORT 8080 # Указываем порт по умолчанию для Cloud Run

# создание рабочей области в докере
WORKDIR /app

# внедрение зависимостей в докер
COPY requirements.txt .
RUN pip install -r requirements.txt

# полное копирование всего остального в дииректорию докера
COPY . .

# запуск приложения с помощью Gunicorn и настройка портов для прослушивания
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:$PORT", "app:app"]