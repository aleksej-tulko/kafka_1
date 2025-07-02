from time import sleep
from threading import Thread

from confluent_kafka import Producer

conf = {
    "bootstrap.servers": "192.168.1.129:9093",
}

producer = Producer(conf)


def create_message(incr_num: int) -> None:
    producer.produce(
        topic='some-topic',
        key=f'key-{incr_num}',
        value=f'message-{incr_num}',
    )
    producer.flush()


incr_num = 0

while True:
    try:
        Thread(target=create_message(incr_num=incr_num))
        incr_num += 1
    except Exception as ex:
        raise RuntimeError(ex)
    finally:
        sleep(10)
