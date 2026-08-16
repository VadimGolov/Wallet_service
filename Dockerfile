FROM python:3.11-slim

WORKDIR /app

# Копируем только requirements.txt для кэширования зависимостей
COPY requirements.txt .

# Устанавливаем зависимости, без кэша pip (меньше образ, ничего лишнего)
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальной код проекта
COPY . .

# Включаем режим без буфера и без записи байт-кода
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Запускаем приложение через uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]