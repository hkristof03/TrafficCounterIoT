import glob
import os
from typing import List

import yaml

from tclib.tctools import tctools as tct


class ConfigReader:

    def __init__(self, path_configs: str = None):
        if path_configs:
            config_files = self.list_config_files(path_configs)
        else:
            config_files = self.list_config_files(os.path.join(
                os.getcwd(), 'system'))
        conf_ = {}
        for file in config_files:
            conf_.update(self.parse_yaml(file))
        self.tct_config = conf_

    @property
    def tct_config(self):
        return self._tct_config

    @tct_config.setter
    def tct_config(self, configuration: dict):
        self._tct_config = configuration

    def get(self, key1: str, key2: str = None) -> str:
        """Reads a value corresponding to a key, or one level embedded key
        from the system configuration.

        :param key1: Existing key in the configuration at level 0
        :param key2: Existing key in the configuration at level 1
        :return: Value corresponding to a given key or embedded key
        """
        if not key2:
            return self.tct_config.get(key1)
        else:
            return self.tct_config.get(key1).get(key2)

    @staticmethod
    def list_config_files(config_directory: str) -> List[str]:
        """Returns a lists of absolute paths to yaml files at a given
        directory.

        :param config_directory: Path to directory that contains .yaml files
        :return: List of .yaml files
        """
        config_files = glob.glob(os.path.join(config_directory, '*.yaml'))
        if not config_files:
            svt.log.warning(
                "WARNING! No configuration files were detected at location: "
                f"{config_directory}"
            )
        return config_files

    @staticmethod
    def parse_yaml(path_yaml: str) -> dict:
        """Reads, parses and returns a yaml file at a given path.

        :param path_yaml:
        :return:
        """
        with open(path_yaml, 'r') as f:
            configs = yaml.load(f.read(), Loader=yaml.Loader)
        return configs
