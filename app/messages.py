import json
import os
from random import choice, choices
import string
from time import sleep
from threading import Thread

from confluent_kafka import (
    Consumer, KafkaError, KafkaException, Producer
)
from dotenv import load_dotenv

load_dotenv()

ACKS_LEVEL = os.getenv('ACKS_LEVEL', 'all')
AUTOOFF_RESET = os.getenv('AUTOCOMMIT_RESET', 'earliest')
ENABLE_AUTOCOMMIT = os.getenv('ENABLE_AUTOCOMMIT', False)
FETCH_MIN_BYTES = os.getenv('FETCH_MIN_BYTES', 1)
FETCH_WAIT_MAX_MS = os.getenv('FETCH_WAIT_MAX_MS', 100)
RETRIES = os.getenv('RETRIES', '3')
SESSION_TIME_MS = os.getenv('SESSION_TIME_MS', 1_000)
TOPIC = os.getenv('TOPIC', 'practice')
FORBIDDEN_WORDS = ["spam", "skam", "windows"]

user_ids = {
    "clown": 1,
    "spammer": 2,
    "dodik": 3,
    "payaso": 4
}

schema_registry_config = {
   'url': 'http://schema-registry:8081'
}

mandatory_message_fields = [
    "sender_id", "sender_name",
    "recipient_id", "recipient_name",
    "amount", "content"
]

conf = {
    "bootstrap.servers":
    "kafka_1:9092,kafka_2:9094,kafka_3:9096",
}

producer_conf = conf | {
    "acks": ACKS_LEVEL,
    "retries": RETRIES,
}

base_consumer_conf = conf | {
    "auto.offset.reset": AUTOOFF_RESET,
    "enable.auto.commit": ENABLE_AUTOCOMMIT,
    "session.timeout.ms": SESSION_TIME_MS
}

single_message_conf = base_consumer_conf | {"group.id": "single"}

batch_conf = base_consumer_conf | {
    "group.id": "batch",
    "fetch.min.bytes": FETCH_MIN_BYTES,
    "fetch.wait.max.ms": FETCH_WAIT_MAX_MS,
}

producer = Producer(producer_conf)
single_message_consumer = Consumer(single_message_conf)
batch_consumer = Consumer(batch_conf)


def delivery_report(err, msg) -> None:
    """Отчет о доставке."""
    if err is not None:
        print(f'Сообщение не отправлено: {err}')
    else:
        print(f'Сообщение доставлено в {msg.topic()} [{msg.partition()}]')


def process_batch(batch: list) -> None:
    """Логгирование батча."""
    for item in batch:
        print(
            'Получено сообщение в батч: '
            f'{item.key().decode('utf-8')}, '
            f'{item.value().decode('utf-8')}, '
            f'offset={item.offset()}. '
            f'Размер сообщения - {len(item.value())} байтов.'
        )


def consume_infinite_loop(consumer: Consumer) -> None:
    """Получение сообщений из брокера по одному."""
    consumer.subscribe([TOPIC])
    try:
        while True:
            msg = consumer.poll(0.1)

            if msg is None or msg.error():
                continue

            value = json.loads(msg.value().decode('utf-8'))
            if isinstance(value, dict) and (
                all(field in mandatory_message_fields
                    for field in value.keys())
            ):
                consumer.commit(asynchronous=False)

                print(
                    f'Получено сообщение: {msg.key().decode('utf-8')}, '
                    f'{value}, offset={msg.offset()}. '
                    f'Размер сообщения - {len(msg.value())} байтов.'
                )
            else:
                print('Ошибка.')
    except KafkaException as KE:
        raise KafkaError(KE)
    finally:
        consumer.close()


def create_message(sender_id: int, sender_name: str,
                   recipient_id: int, recipient_name: str,
                   amount: float, content: str
                   ) -> None:
    """Сериализация сообщения и отправка в брокер."""
    message_value = {
        "sender_id": sender_id,
        "sender_name": sender_name,
        "recipient_id": recipient_id,
        "recipient_name": recipient_name,
        "amount": amount,
        "content": content
        }
    producer.produce(
        topic=TOPIC,
        key="pract",
        value=json.dumps(message_value).encode('utf-8'),
        on_delivery=delivery_report
    )


def producer_infinite_loop():
    """Запуска цикла для генерации сообщения."""
    incr_num: float = 0.0
    user_names = list(user_ids)
    try:
        while True:
            for sender_name, id in user_ids.items():
                recipients = [name for name in user_names
                              if name != sender_name]
                for recipient_name in recipients:
                    content = (
                        choice(FORBIDDEN_WORDS) if incr_num % 10 == 0
                        else ''.join(
                            choices(
                                string.ascii_uppercase + string.digits, k=5)
                        )
                    )
                    create_message(
                        sender_id=id,
                        sender_name=sender_name,
                        recipient_id=user_ids[recipient_name],
                        recipient_name=recipient_name,
                        amount=incr_num,
                        content=content)
                    incr_num += 1.0
                    if incr_num % 10 == 0:
                        producer.flush()
    except (KafkaException, Exception) as e:
        raise KafkaError(e)
    finally:
        producer.flush()


if __name__ == '__main__':
    """Основной код."""
    single_message_consumer_thread = Thread(
        target=consume_infinite_loop,
        args=(single_message_consumer,),
        daemon=True
    )
    producer_thread = Thread(
        target=producer_infinite_loop,
        args=(),
        daemon=True
    )
    single_message_consumer_thread.start()
    producer_thread.start()

    while True:
        print('Выполняется программа')
        sleep(10)
