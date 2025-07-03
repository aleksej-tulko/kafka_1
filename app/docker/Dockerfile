FROM python:3.9

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --no-cache-dir

COPY ../app/messages.py .

CMD ["python3", "messages.py"]

