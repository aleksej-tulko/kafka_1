# Описание

Программа с одним продюсером сообщений, которые отправляются в кластер из трех брокеров Kafka, и двумя конюмерами. Запускается в двух репликах.

Один из консюмеров считывает сообщения по одному, второй - пачкой.

Даннее о кластере Kafka хранятся в Zookeeper.

Сериализация и десериализация выполняются с помощью schema registry.

Веб UI брокера доступен по адресу *http://$server_ip:8080*

## Требования

- **OS**: Linux Ubuntu 24.04 aarm
- **Python**: Python 3.12.3
- **Docker**: 28.2.2 - https://docs.docker.com/engine/install/ubuntu/

## Подготовка к запуску

1. Склонировать репозиторий:
    ```bash
    git clone git@github.com:aleksej-tulko/kafka_1.git
    ```
2. Перейти в директорию с программой:
    ```bash
    cd kafka_1.git
    ```
3. Создать файл .env c переменными,
    ```env
    ACKS_LEVEL='all'
    AUTOOFF_RESET='earliest'
    ENABLE_AUTOCOMMIT=False
    FETCH_MIN_BYTES=400
    FETCH_WAIT_MAX_MS=100
    RETRIES=3
    SESSION_TIME_MS=6000
    TOPIC='pract-task2'
    ```
4. Создать рабочее окружение и активировать его:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
5. Установить зависимости:
    ```bash
    pip install -r requirements.txt
    ```
6. Создать папки на хосте
    ```bash
    mkdir -p /opt/kafka/kafka_1/
    mkdir -p /opt/kafka/kafka_2/
    mkdir -p /opt/kafka/kafka_3/
    mkdir -p /opt/zookeeper/data
    mkdir -p /opt/zookeeper/log
    chown 1000:1000 /opt/kafka/ -R
    chown 1000:1000 /opt/zookeeper/ -R
    ```

7. Создать docker network
    ```bash
    docker network create kafka-network
    ```

8. Запустить сервисы
    ```bash
    docker compose up zookeeper kafka_1 kafka_2 kafka_3 schema_registry
    ```
    При первом запуске до создания топика программу **app** запускать не надо. После создания топика при последуюший перезапусках можно использовать
    ```bash
    docker compose up -d
    ```

9. Создать топик
    ```bash
    docker exec -it kafka_1-kafka_1-1 kafka-topics --describe --topic pract-task2 --bootstrap-server localhost:9092
    ```

10. Запустить программу
    ```bash
    docker compose up app -d
    ```

11. Проверить логи
    ```bash
    docker compose logs -f
    ```

## Автор
[Aliaksei Tulko](https://github.com/aleksej-tulko)