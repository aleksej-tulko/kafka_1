from time import sleep
from threading import Thread

from confluent_kafka import (
    Consumer, KafkaError, KafkaException, Producer
)
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONSerializer
from confluent_kafka.serialization import (
    MessageField, SerializationContext, StringSerializer
)

schema_registry_config = {
   'url': 'http://localhost:8081'
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


conf = {
    "bootstrap.servers":
    "kafka_1:9092,kafka_2:9094,kafka_3:9096",
}

producer_conf = conf | {
    "acks": "all",
    "retries": 3,
}

base_consumer_conf = conf | {
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,
    "session.timeout.ms": 6_000
}

single_message_conf = base_consumer_conf | {"group.id": "single"}
batch_conf = base_consumer_conf | {
    "group.id": "batch",
    "fetch.min.bytes": 1,
    "fetch.wait.max.ms": 100,
}

producer = Producer(producer_conf)
single_message_consumer = Consumer(single_message_conf)
batch_consumer = Consumer(batch_conf)

TOPIC = 'pract-task'


def delivery_report(err, msg):
    if err is not None:
        print(f'Сообщение не отправлено: {err}')
    else:
        print(f'Сообщение доставлено в {msg.topic()} [{msg.partition()}]')


def consume_infinite_loop(consumer: Consumer) -> None:
    consumer.subscribe([TOPIC])
    try:
        while True:
            msg = consumer.poll(0.1)

            if msg is None:
                continue
            if msg.error():
                continue

            print(
                f'Получено сообщение: {msg.key().decode('utf-8')}, '
                f'{msg.value().decode('utf-8')}, offset={msg.offset()}'
            )
    except KafkaException as KE:
        raise KafkaError(KE)
    finally:
        consumer.commit(asynchronous=False)
        consumer.close()


def consume_batch_loop(consumer: Consumer, batch_size=10):
    consumer.subscribe([TOPIC])
    batch = []
    try:
        while True:
            msg = consumer.poll(0.1)

            if msg is None:
                continue
            if msg.error():
                continue

            batch.append(msg)

            if len(batch) == batch_size:
                for item in batch:
                    print(
                        'Получено сообщение в батч: '
                        f'{item.key().decode('utf-8')}, '
                        f'{item.value().decode('utf-8')}, '
                        f'offset={item.offset()}'
                    )
                batch.clear()
    except KafkaException as KE:
        raise KafkaError(KE)
    finally:
        consumer.commit(asynchronous=False)
        consumer.close()


def create_message(incr_num: int) -> None:
    message_value = {"id": incr_num, "name": "product-{incr_num}"}
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
