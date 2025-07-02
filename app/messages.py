from time import sleep
from threading import Thread
from confluent_kafka import Consumer, Producer

conf = {
    "bootstrap.servers":
    "192.168.1.129:9093,192.168.1.129:9095,192.168.1.129:9097",
}

base_consumer_conf = conf | {"auto.offset.reset": "earliest"}
single_message_conf = base_consumer_conf | {"group.id": "single"}
batch_conf = base_consumer_conf | {"group.id": "batch"}

producer = Producer(conf)
single_message_consumer = Consumer(single_message_conf)
batch_consumer = Consumer(batch_conf)


def create_message(incr_num: int) -> None:
    producer.produce(
        topic='pract-task',
        key=f'key-{incr_num}',
        value=f'message-{incr_num}',
    )
    producer.flush()


def producer_thread(num):
    Thread(target=create_message, args=(num,)).start()


incr_num = 0

try:
    while True:
        producer_thread(incr_num)
        incr_num += 1
        sleep(0.1)
except Exception as ex:
    raise RuntimeError(ex)
finally:
    sleep(10)
    producer.flush()
    producer.close()