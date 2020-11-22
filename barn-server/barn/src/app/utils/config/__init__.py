import configparser
import os
from flask import Config



class ConfigLoader():
    """Config loader class for barn-server.cfg"""

    MONGO_DEFAULT_CONFIG = {
        "mongo_user": "admin",
        "mongo_password": "change_me",
        "mongo_host": "127.0.0.1",
        "mongo_port": "27017",
        "mongo_db": "inventory"
    }

    BARN_DEFAULT_CONFIG = {
        "barn_init_admin_user": "admin",
        "barn_init_admin_password": "admin",
        "https_cert": None,
        "https_cert_key": None,
        "barn_token_encryption_key": "change_me"
    }

    def __init__(self, config_path):
        self.config_path = config_path
        self.barn_config = self._get_barn_config(self.config_path)
        self.mongo_config = self._get_mongo_config(self.config_path)

    @classmethod
    def _load_config(cls, config_path, section):
        """
            Load ini config file to dir
            When file doesn't exist, return empty directory
        """
        result = {}
        if os.path.isfile(config_path):
            config = configparser.ConfigParser()
            config.read(config_path)
            for k, v in config.items(section):
                if v in ["yes", "true", "on"]:
                    result[k] = True
                elif v in ["no", "false", "off"]:
                    result[k] = False
                elif v.isdigit():
                    result[k] = int(v)
                elif v.replace('.', '', 1).isdigit() or v.replace(',', '', 1).isdigit():
                    result[k] = float(v.replace(',', '.', 1))
                else:
                    result[k] = v
        return result

    def _get_mongo_config(self, config_path):
        mongo_config = ConfigLoader.MONGO_DEFAULT_CONFIG.copy()
        mongo_config.update(self._load_config(config_path, "mongodb"))
        return mongo_config

    def _get_barn_config(self, config_path):
        barn_config = ConfigLoader.BARN_DEFAULT_CONFIG.copy()
        barn_config.update(self._load_config(config_path, "barn"))
        return barn_config

    def get_config(self):
        return dict(
            BARN_CONFIG=self.barn_config,
            TOKEN_ENCRYPTION_KEY=self.barn_config.get("barn_token_encryption_key"),
            MONGODB_SETTINGS=dict(
                db=self.mongo_config.get("mongo_db"),
                host=self.mongo_config.get("mongo_host"),
                username=self.mongo_config.get("mongo_user"),
                password=self.mongo_config.get("mongo_password"),
                authentication_source="admin"
            )
        )