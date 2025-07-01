from confluent_kafka import Producer

conf = {
    "bootstrap.servers": "192.168.1.129:9093",
} 

producer = Producer(conf)


producer.produce(
    topic="some-topic",
    key="key-1",
    value="message-1",
)

producer.flush()