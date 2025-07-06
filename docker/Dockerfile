FROM python:3.13

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

### Копирование файла с энв переменными не допустимо
### в проде, но это просто чтоб ревьювер не возился
### с переменными.
COPY ../app/.env .

COPY ../app/messages.py .

CMD ["python3", "messages.py"]

