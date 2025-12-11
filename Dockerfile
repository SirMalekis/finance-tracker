# Используем официальный легковесный образ Python
FROM python:3.9-slim

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PORT 8080 # Указываем порт по умолчанию для Cloud Run

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install -r requirements.txt

# Копируем остальной код приложения в рабочую директорию
COPY . .

# Команда для запуска приложения с помощью Gunicorn
# Gunicorn будет слушать на порту, который указан в переменной $PORT
CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:$PORT", "app:app"]