from typing import List, Union, Tuple, Callable
import traceback

import json
from confluent_kafka import Producer, Consumer, KafkaException
from confluent_kafka.admin import AdminClient, NewTopic

from tclib.tctools import tctools as tct

log = tct.log


class KafkaHelper(object):
    def __init__(self, target_landscape='custom', config_section=None):
        self.kafka_config = {
            'bootstrap.servers': tct.conf.get('kafka', 'bootstrap.servers')
        }
        self.producer = None
        log.info(
            "Initialized new KafkaHelper object with config: "
            f"{self.kafka_config}"
        )

    def publish(self, topic: str, message: Union[dict, str]) -> None:
        """Posts the passed message to the target Kafka topic.

        :param topic: Identifier of the target topic
        :param message: Message in a dictionary or string format
        """
        assert isinstance(message, str) or isinstance(message, dict)

        if not self.producer:
            self.producer = Producer(self.kafka_config)

        if isinstance(message, dict):
            message = json.dumps(message)
        # Asynchronous message producing
        self.producer.produce(topic, message.encode('utf-8'))
        self.producer.flush()
        log.info(f"Posted a document to kafka topic: {topic}")

    def consume_forever(
        self,
        group_id: str,
        topics: List[str],
        callback_functions: List[Callable]
    ) -> None:
        """

        :param group_id:
        :param topics:
        :param callback_functions:
        :return:
        """
        assert len(topics) == len(callback_functions)
        callbacks = dict(zip(topics, callback_functions))
        self.kafka_config.update({
            'group.id': group_id,
            'auto.offset.reset': 'earliest'
        })
        c = Consumer(self.kafka_config)
        c.subscribe(topics)
        # Read messages
        try:
            while True:
                msg = c.poll(timeout=1.0)
                if not msg:
                    log.info(
                        "There was no message on the subscribed Kafka topics!"
                    )
                elif msg.error():
                    raise KafkaException(msg.error())
                else:
                    message = json.loads(msg.value().decode('utf-8'))
                    callbacks[msg.topic()](message)

        except Exception as error:
            log.error(
                f"Unexpected event occurred! Error: {traceback.format_exc()}"
            )
        finally:
            # Shut down the consumer to commit the current offsets
            c.close()


class KafkaAdmin:
    def __init__(self):
        self.kafka_config = {
            'bootstrap.servers': tct.conf.get('kafka', 'bootstrap_servers')
        }
        self.admin = AdminClient(self.kafka_config)

    def create_topics(self, topics: List[Tuple[str, int, int]]) -> None:
        """Creates a list of kafka topics.

        :param topics: List of tuples where:
            1. element: name of the topic to create
            2. element: number of partitions
            3. element: number of replicas in the cluster
        """
        producer = Producer(
            {'bootstrap.servers': tct.conf.get('kafka', 'bootstrap_servers')}
        )
        existing_topics = producer.list_topics().topics
        new_topics = [
            (topic, 1, 1) for topic in topics if topic not in existing_topics
        ]
        nts = [NewTopic(top[0], top[1], top[2]) for top in topics]

        if nts:
            self.admin.create_topics(nts)
            log.info(f"Created topics: {topics}")
        else:
            log.info(f"Topics: {topics} are already existed!")

    def delete_topics(self, topics: List[str]) -> None:
        """Deletes a list of topics.

        :param topics: List of strings where strings indicate topics
        """
        self.admin.delete_topics(topics)








