from time import sleep
from threading import Thread

from confluent_kafka import Consumer, Producer

conf = {
    "bootstrap.servers":
    "192.168.1.129:9093,192.168.1.129:9095,192.168.1.129:9097",
}

producer_conf = conf
consumer_conf = conf.update({"auto.offset.reset": "earliest"})

producer = Producer(conf)
SingleMessageConsumer = Consumer(consumer_conf)
BatchMessageConsumer = Consumer(consumer_conf)


def create_message(incr_num: int) -> None:
    producer.produce(
        topic='pract-task',
        key=f'key-{incr_num}',
        value=f'message-{incr_num}',
    )
    producer.flush()
    producer.close()


incr_num = 0

while True:
    try:
        Thread(target=create_message(incr_num=incr_num))
        incr_num += 1
    except Exception as ex:
        raise RuntimeError(ex)
    finally:
        sleep(10)
