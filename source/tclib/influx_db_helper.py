import os
import traceback
from requests.exceptions import ConnectionError
from typing import List

from influxdb import InfluxDBClient
from influxdb.exceptions import InfluxDBClientError
import numpy as np

from atomlib.atomtools import atomtools as atom

conf = atom.conf
log = atom.log


class InfluxDBLoader:
    base_path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, client_conf: dict, input_conf, output_conf, **kwargs):
        self.client_conf = client_conf
        self.input_conf = input_conf
        self.output_conf = output_conf
        self.client = None

    def connect_to_influxdb(self, database: str) -> None:
        """Tries to connect to the passed database.
        """
        try:
            log.info("Initializing InfluxDBClient...")
            self.client = InfluxDBClient(**self.client_conf)
            #self.check_database_existence(database)
            self.client.switch_database(database)
            log.info(f"Connected to Influxdb database: {database}")
        except InfluxDBClientError:
            log.critical(
                f"Connection to InfluxDB failed! {traceback.print_exc()}"
            )

    def test_connection(self, database) -> None:
        """Pings the server and tries to reconnect in case of a failure.
        """
        try:
            self.client.ping()
        except ConnectionError:
            self.connect_to_influxdb(database)

    def check_database_existence(self, database: str) -> None:
        """Checks the existence of the passed database and creates it if it
        does not exist yet.

        :param database: Name of the database
        """
        databases = self.client.get_list_database()
        if not any(v == database for d in databases for k, v in d.items()):
            log.info(f"Creating database: {database}")
            self.client.create_database(database)
        else:
            log.info(f"Database {database} already exists!")

    def write_to_influxdb(
        self,
        data: List[dict],
        database: str
    ) -> None:
        """Writes the passed data to the given database.

        :param data: data in a list of dictionaries
        :param database:  name of the database to write to
        """
        try:
            self.test_connection(database)
            log.info(f"Writing to database: {database}")
            self.client.write_points(data, **self.output_conf['write_conf'])
            log.info(
                f"Succesfully inserted {len(data)} objects to database "
                f"{database}"
            )
        except Exception:
            log.error(
                f"Unexpected event occurred while writing database {database}:"
                f" {traceback.print_exc()}"
            )

    def query_from_influxdb(self, query: str, database: str) -> list:
        """Performs the passed query on the given database.

        :param query: SQL like influxdb query
        :param database: database from which to query
        """
        try:
            self.test_connection(database)
            log.info(f"Querying from database: {database}")
            result = list(self.client.query(query).get_points())
            return result
        except Exception:
            log.error(
                "Unexpected event  occurred while querying from database -"
                f" {database}: {traceback.print_exc()}"
            )

    def map_json_to_schema(self, data: dict, measurement: str) -> dict:
        """Structures the passed data to a json like dictionary format which
        influxdb requires. The schema should be described in the application's
        yaml configuration file from which the class is built up (tags, fields
        , time and type mapping for key-value pairs).

        :param data: data in a key-value format to write to influxdb
        :param measurement: name of the measurement to write the data to
        :return: influxdb required json like format
        """
        try:
            schema = self.output_conf['schema']
            type_map = self.output_conf['type_map']
            json_object = {}
            json_object.update(measurement)
            for key in schema:
                if type(schema[key]) == str:
                    json_object.update(
                        {key: str(data[schema[key]])}
                    )
                if type(schema[key]) == list:
                    d_ = {}
                    for i in schema[key]:
                        if i not in data.keys():
                            continue
                        if i in type_map:
                            if type_map[i] == 'int':
                                d_[i] = int(data[i])
                            elif type_map[i] == 'int64':
                                d_[i] = np.int64(data[i])
                            elif type_map[i] == 'float':
                                d_[i] = float(data[i])
                        else:
                            d_[i] = str(data[i])
                    json_object.update({key: d_})

            return json_object

        except Exception:
            log.error(
                "Unexpected event occurred while parsing data:"
                f"{traceback.print_exc()}"
            )
