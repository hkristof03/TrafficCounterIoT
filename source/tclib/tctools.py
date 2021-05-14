import inspect
from pathlib import Path


class TrafficCounterTools(object):

    def __init__(self):
        self.logger = None
        self.config_reader = None
        self.kafka_helper = None
        self.kafka_admin = None
        self.scheduler = None
        self.os_env = None
        self.schema_factory = None

    @property
    def log(self):
        # log the name of the caller
        caller_frame = inspect.stack()[1]
        logger_name = f"TrafficCounter.{Path(caller_frame.filename).stem}"

        if self.logger and self.logger.name == logger_name:
            return self.logger
        else:
            import logging
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(process)d - %(levelname)s '
                       '- %(message)s'
            )
            self.logger = logging.getLogger(logger_name)
            return self.logger

    @property
    def conf(self):
        if not self.config_reader:
            from tclib.config_reader import ConfigReader
            self.config_reader = ConfigReader()
        return self.config_reader

    @property
    def kafka(self):
        if not self.kafka_helper:
            from tclib.kafka_helper import KafkaHelper
            self.kafka_helper = KafkaHelper()
        return self.kafka_helper

    @property
    def admin(self):
        if not self.kafka_admin:
            from tclib.kafka_helper import KafkaAdmin
            self.kafka_admin = KafkaAdmin()
        return self.kafka_admin

    @property
    def chrono(self):
        if not self.scheduler:
            from tclib.scheduler import Scheduler
            self.scheduler = Scheduler()
        return self.scheduler

    @property
    def env(self):
        if not self.os_env:
            from tclib.os_env_helper import OSEnvHelper
            self.os_env = OSEnvHelper()
        return self.os_env

    @property
    def schema(self):
        if not self.schema_factory:
            from tclib.schema_helper import SchemaHelperFactory
            self.schema_factory = SchemaHelperFactory()
        return self.schema_factory


tctools = TrafficCounterTools()
