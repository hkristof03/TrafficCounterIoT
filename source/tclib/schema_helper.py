import os
from abc import ABC, ABCMeta
import json
import jsonschema

from tclib.tctools import tctools as tct


log = tct.log


class TrafficCounterSchemaError(Exception):
    """Error raised when a json document does not match its corresponding
    schema.
    """
    def __init__(self, message: str, payload: str = None) -> None:
        self.message = message
        self.payload = payload

    def __repr__(self):
        return str(self.message + self.payload)


class CameraImageSchemaError(TrafficCounterSchemaError):
    """Error raised when a document that carries an X-ray image of a carried
    object does not matches its defined schema.
    """
    def __init__(self, message: str, payload: str = None) -> None:
        super().__init__(message, payload)


class TrafficDetectionSchemaError(TrafficCounterSchemaError):
    """Error raised when a document that carries a prediction for an X-ray
    image does not matches its defined schema.
    """
    def __init__(self, message: str, payload: str = None) -> None:
        super().__init__(message, payload)


class SchemaErrorFactory(object):

    builder = {
        'XRayScan': CameraImageSchemaError,
        'ThreatPrediction': TrafficDetectionSchemaError
    }

    @classmethod
    def create_error(cls, error_type: str, **kwargs):
        return SchemaErrorFactory.builder[error_type](**kwargs)


class AbstractSchemaHelper(ABC):

    def __init__(
        self,
        path_schema: str,
        error: str
    ) -> None:
        self.schema = path_schema
        self.schema_name = path_schema.split(os.sep)[-1]
        self.error = error
        self.validator = jsonschema.Draft7Validator(self.schema)
        self.sef = SchemaErrorFactory()

    @property
    def schema(self):
        return self._schema

    @schema.setter
    def schema(self, path_schema: str):
        """It reads the schema related to the class and validates its
        correctness according to its version.

        :param path_schema: Path where from where the schema can be loaded
        """
        try:
            with open(path_schema, 'r', encoding='utf-8') as file:
                schema = json.load(file)
            jsonschema.Draft7Validator.check_schema(schema)
            log.info(
                f"Schema definition {path_schema.split(os.sep)[-1]} is loaded "
                "and it is valid!"
            )
            self._schema = schema
        except jsonschema.exceptions.SchemaError as error:
            log.error(
                "Invalid schema definition for file: "
                f"{path_schema.split(os.sep)[-1]}!"
            )
            raise error

    def validate(self, json_data: dict):
        """Validates the passed JSON data according to the corresponding
        schema. Raises an error it the document is not valid.

        :param json_data: A document of a Kafka message
        """
        try:
            self.validator.validate(json_data)
            log.info(f"Validated the message with schema: {self.schema_name}")
        except jsonschema.exceptions.ValidationError as error:
            d = {
                "message":
                    "Document is not valid according to the defined schema!",
                "payload": f"{error}"
            }
            raise self.sef.create_error(self.error, **d)


class CameraImageSchemaHelper(AbstractSchemaHelper):

    def __init__(self):
        super().__init__(
            os.path.join(os.getcwd(), 'schemas', 'camera_image.json'),
            'CameraImage'
        )


class TrafficDetectionSchemaHelper(AbstractSchemaHelper):

    def __init__(self):
        super().__init__(
            os.path.join(
                os.getcwd(), 'schemas', 'traffic_detection.json'
            ),
            'TrafficDetection'
        )


class SchemaHelperFactory(object):

    builder = {
        'CameraImage': CameraImageSchemaHelper,
        'TrafficDetection': TrafficDetectionSchemaHelper
    }

    @classmethod
    def create_helper(cls, helper_type: str):
        return SchemaHelperFactory.builder[helper_type]()
