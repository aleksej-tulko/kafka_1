import os
from time import sleep
from threading import Thread

from confluent_kafka import (
    Consumer, KafkaError, KafkaException, Producer
)
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import (
    JSONDeserializer, JSONSerializer
)
from confluent_kafka.serialization import (
    MessageField, SerializationContext, StringSerializer
)
from dotenv import load_dotenv

load_dotenv()

ACKS_LEVEL = os.getenv('ACKS_LEVEL', 'all')
AUTOCOMMIT_RESET = os.getenv('AUTOCOMMIT_RESET', 'earliest')
ENABLE_AUTOCOMMIT = os.getenv('ENABLE_AUTOCOMMIT', False)
FETCH_MIN_BYTES = os.getenv('FETCH_MIN_BYTES', 1)
FETCH_WAIT_MAX_MS = os.getenv('FETCH_WAIT_MAX_MS', 100)
RETRIES = os.getenv('RETRIES', '3')
SESSION_TIME_MS = os.getenv('SESSION_TIME_MS', 1_000)
TOPIC = os.getenv('TOPIC', 'practice')

schema_registry_config = {
   'url': 'http://schema-registry:8081'
}

json_schema_str = """
{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Product",
    "type": "object",
    "properties": {
        "id": {
            "type": "integer"
        },
        "name": {
            "type": "string"
        }
    },
    "required": ["id", "name"]
}
"""

schema_registry_client = SchemaRegistryClient(schema_registry_config)
json_serializer = JSONSerializer(json_schema_str, schema_registry_client)
key_serializer = StringSerializer('utf_8')
value_serializer = json_serializer


def from_dict(obj: dict, ctx: SerializationContext) -> dict:
    return obj


json_deserializer = JSONDeserializer(
    json_schema_str,
    schema_registry_client,
    from_dict=from_dict)


conf = {
    "bootstrap.servers":
    "kafka_1:9092,kafka_2:9094,kafka_3:9096",
}

producer_conf = conf | {
    "acks": ACKS_LEVEL,
    "retries": RETRIES,
}

base_consumer_conf = conf | {
    "auto.offset.reset": AUTOCOMMIT_RESET,
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


def delivery_report(err, msg):
    if err is not None:
        print(f'Сообщение не отправлено: {err}')
    else:
        print(f'Сообщение доставлено в {msg.topic()} [{msg.partition()}]')


def process_batch(batch: list) -> None:
    for item in batch:
        print(
            'Получено сообщение в батч: '
            f'{item.key().decode('utf-8')}, '
            f'{item.value().decode('utf-8')}, '
            f'offset={item.offset()}. '
            f'Размер сообщения - {len(item.value())} байтов.'
        )


def consume_infinite_loop(consumer: Consumer) -> None:
    consumer.subscribe([TOPIC])
    try:
        while True:
            msg = consumer.poll(0.1)

            if msg is None or msg.error():
                continue
            print(msg.value().decode('utf-8'))
            deserialized = json_deserializer(
                msg.value().decode('utf-8'),
                SerializationContext(TOPIC, MessageField.VALUE)
            )

            if isinstance(deserialized, dict) and (
                all(field in ('id', 'name') for field in deserialized.keys())
            ):
                consumer.commit(asynchronous=False)

                print(
                    f'Получено сообщение: {msg.key().decode('utf-8')}, '
                    f'{deserialized}, offset={msg.offset()}. '
                    f'Размер сообщения - {len(msg.value())} байтов.'
                )
            else:
                print('Ошибка десериализации.')
    except KafkaException as KE:
        raise KafkaError(KE)
    finally:
        consumer.close()


def consume_batch_loop(consumer: Consumer, batch_size=10):
    consumer.subscribe([TOPIC])
    batch = []
    try:
        while True:
            msg = consumer.poll(0.1)

            if msg is None or msg.error():
                continue
            print(msg.value().decode('utf-8'))
            deserialized = json_deserializer(
                msg.value().decode('utf-8'),
                SerializationContext(TOPIC, MessageField.VALUE),

            )

            if isinstance(deserialized, dict) and (
                all(field in ('id', 'name') for field in deserialized.keys())
            ):
                batch.append(msg)
            else:
                print('Ошибка десериализации.')

            if len(batch) == batch_size:
                process_batch(batch=batch)
                consumer.commit(asynchronous=False)
                batch.clear()
    except KafkaException as KE:
        raise KafkaError(KE)
    finally:
        if batch:
            process_batch(batch=batch)
            consumer.commit(asynchronous=False)
            batch.clear()
        consumer.close()


def create_message(incr_num: int) -> None:
    message_value = {"id": incr_num, "name": f"product-{incr_num}"}
    producer.produce(
        topic=TOPIC,
        key=key_serializer(
            "user_key", SerializationContext(TOPIC, MessageField.VALUE)
        ),
        value=value_serializer(
            message_value, SerializationContext(TOPIC, MessageField.VALUE)
        ),
        on_delivery=delivery_report
    )


def producer_infinite_loop():
    incr_num = 0
    try:
        while True:
            create_message(incr_num)
            incr_num += 1
            if incr_num % 10 == 0:
                producer.flush()
            sleep(0.1)
    except KafkaException as KE:
        raise KafkaError(KE)
    finally:
        producer.flush()


if __name__ == '__main__':
    single_message_consumer_thread = Thread(
        target=consume_infinite_loop,
        args=(single_message_consumer,),
        daemon=True
    )
    batch_consumer_thread = Thread(
        target=consume_batch_loop,
        args=(batch_consumer,),
        daemon=True
    )
    producer_thread = Thread(
        target=producer_infinite_loop,
        args=(),
        daemon=True
    )
    single_message_consumer_thread.start()
    batch_consumer_thread.start()
    producer_thread.start()

    while True:
        print('Выполняется программа')
        sleep(10)
