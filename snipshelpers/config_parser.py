from configparser import ConfigParser
import os
import traceback

CONFIG_FILE = 'config.ini'
CONFIGURATION_ENCODING_FORMAT = "utf-8"
SECRET_SECTION = 'secret'
GLOBAL_SECTION = 'global'
BRIDGE_IP_KEY = 'bridge_ip'
API_KEY_KEY = 'api_key'


class SnipsConfigParser():

    @staticmethod
    def _convert_to_dict(config):
        try:
            if config.has_section(GLOBAL_SECTION) and config.has_section(SECRET_SECTION):
                return {BRIDGE_IP_KEY: config[GLOBAL_SECTION].get(BRIDGE_IP_KEY, None),
                        API_KEY_KEY: config[SECRET_SECTION].get(API_KEY_KEY, None)}
            else:
                return dict()
        except Exception:
            traceback.print_exc()
            return dict()

    @staticmethod
    def _convert_from_dict(config_dict):
        try:
            config = ConfigParser()
            config.add_section(GLOBAL_SECTION)
            config.add_section(SECRET_SECTION)
            config[GLOBAL_SECTION][BRIDGE_IP_KEY] = config_dict[BRIDGE_IP_KEY]
            config[SECRET_SECTION][API_KEY_KEY] = config_dict[API_KEY_KEY]
        except Exception:
            traceback.print_exc()
        return config

    @staticmethod
    def read_configuration_file():
        if not os.path.isfile(CONFIG_FILE):
            SnipsConfigParser.write_configuration_file(SnipsConfigParser._convert_from_dict(None))
        try:
            with open(CONFIG_FILE, encoding=CONFIGURATION_ENCODING_FORMAT, mode='r') as f:
                config = ConfigParser()
                config.read_file(f)
                return SnipsConfigParser._convert_to_dict(config)
        except (IOError, ConfigParser.Error):
            traceback.print_exc()
            return ConfigParser()

    @staticmethod
    def write_configuration_file_from_dict(config_dict):
        config = SnipsConfigParser._convert_from_dict(config_dict)
        with open(CONFIG_FILE, 'w', encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            config.write(f)

    @staticmethod
    def write_configuration_file(bridge_ip, api_key):
        SnipsConfigParser.write_configuration_file_from_dict({BRIDGE_IP_KEY: bridge_ip, API_KEY_KEY: api_key})
