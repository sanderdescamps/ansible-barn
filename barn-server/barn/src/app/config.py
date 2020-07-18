import configparser
import os

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


class ConfigLoader():
    """Config loader class for barn-server.cfg"""

    def __init__(self, config_path):
        self.config_path = config_path
        self.barn_config = None
        self.mongo_config = None

    def _load_config(self, section):
        """
            Load ini config file to dir
            When file doesn't exist, return empty directory
        """
        result = {}
        if os.path.isfile(self.config_path):
            config = configparser.ConfigParser()
            config.read(self.config_path)
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

    def get_mongo_config(self):
        if self.mongo_config is None:
            self.mongo_config = MONGO_DEFAULT_CONFIG.copy()
            self.mongo_config.update(self._load_config("mongodb"))
        return self.mongo_config

    def get_mongo_settings(self):
        mongo_config = self.get_mongo_config()
        return dict(
            db=mongo_config.get("mongo_db"),
            host=mongo_config.get("mongo_host"),
            username=mongo_config.get("mongo_user"),
            password=mongo_config.get("mongo_password"),
            authentication_source="admin"
        )

    def get_barn_config(self):
        if self.barn_config is None:
            self.barn_config = BARN_DEFAULT_CONFIG.copy()
            self.barn_config.update(self._load_config("barn"))
        return self.barn_config
