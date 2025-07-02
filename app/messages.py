from time import sleep
from threading import Thread
from confluent_kafka import Consumer, Producer, KafkaException

conf = {
    "bootstrap.servers": "192.168.1.129:9093,192.168.1.129:9095,192.168.1.129:9097",
}

base_consumer_conf = conf | {"auto.offset.reset": "earliest"}
single_message_conf = base_consumer_conf | {"group.id": "single"}
batch_conf = base_consumer_conf | {"group.id": "batch"}

producer = Producer(conf)
single_message_consumer = Consumer(single_message_conf)
batch_consumer = Consumer(batch_conf)

TOPIC = 'pract-task'


def consume_infinite_loop(consumer: Consumer) -> None:
    consumer.subscribe([TOPIC])
    try:
        while True:
            msg = consumer.poll(0.1)

            if msg is None:
                continue
            if msg.error():
                print(f"Ошибка: {msg.error()}")
                continue

            key = msg.key().decode("utf-8")
            value = msg.value().decode("utf-8")
            print(
                f"Получено сообщение: {key=}, {value=}, offset={msg.offset()}"
            )
    finally:
        consumer.close()


def create_message(incr_num: int) -> None:
    producer.produce(
        topic=TOPIC,
        key=f'key-{incr_num}',
        value=f'message-{incr_num}',
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
    finally:
        producer.flush()
        producer.close()
        print("Producer closed")


if __name__ == "__main__":
    t1 = Thread(target=consume_infinite_loop, args=(single_message_consumer, "SingleConsumer"), daemon=True)
    t2 = Thread(target=consume_infinite_loop, args=(batch_consumer, "BatchConsumer"), daemon=True)
    t1.start()
    t2.start()

    producer_infinite_loop()
