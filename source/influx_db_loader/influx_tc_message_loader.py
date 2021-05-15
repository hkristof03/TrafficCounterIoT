import os
import traceback
from dateutil import parser, tz

from influx_db_helper import InfluxDBLoader
from tclib.tctools import tctools as tct
from tclib.scheduler import TC_TIME_ZONE


class TrafficCountMessageLoader:
    def __init__(
        self,
        group_id: str,
        kafka_input_topic: str,
        influx_db_config: dict
    ) -> None:
        self.group_id = group_id
        self.kafka_input_topic = kafka_input_topic
        self.influx_db_config = influx_db_config
        self.influx_db_config.update(tct.conf.get("influx_db"))
        self.idbl = InfluxDBLoader(**influx_db_config)
        self.idbl.connect_to_influxdb(self.idbl.input_conf["database"])
        self.messages = []

    def run(self) -> None:
        tct.kafka.consume_forever(
            group_id=self.group_id,
            topics=[self.kafka_input_topic],
            callback_functions=[self.consume_traffic_count_messages]
        )

    def consume_traffic_count_messages(self, message: dict) -> None:
        """

        :param message:
        :return:
        """
        tct.log.info(f"Received message: {message}")
        time = self.idbl.output_conf['schema']["time"]
        message[time] = parser.isoparse(
            message[time]).replace(tzinfo=tz.gettz(TC_TIME_ZONE))
        self.messages.append(message)

        if len(self.messages) > 10:
            self.write_data_to_influx_db()
            self.messages = []

    def write_data_to_influx_db(self) -> None:
        """

        :return:
        """
        try:
            out_meas = self.idbl.output_conf["measurement"]
            data = [
                self.idbl.map_json_to_schema(d,
                                             out_meas) for d in self.messages
            ]
            self.idbl.write_to_influxdb(data,
                                        self.idbl.output_conf["database"])
        except:
            tct.log.error(
                f"Unexpected event occurred! Error: {traceback.format_exc()}"
            )


if __name__ == '__main__':

    app_conf = tct.conf.parse_yaml(
        os.path.join(os.getcwd(), 'configs', 'app_config.yml')
    )['InfluxDBLoaderTC']

    ml = TrafficCountMessageLoader(**app_conf)
    ml.run()
