import os
import sys
import configparser
from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint
from app.pages.admin.users import user_pages
from app.pages.admin.export import export_pages
from app.pages.inventory.hosts import host_pages
from app.pages.inventory.groups import group_pages
from app.pages.inventory.nodes import node_pages
from app.pages.inventory_export import inventory_pages
from app.pages.debug import debug_pages
from app.pages.upload import upload_pages
from app.pages.login import login_pages
from app.models import User


DEFAULT_BARN_CONFIG={
    "barn_init_admin_user": "admin",
    "barn_init_admin_password": "admin",
    "debug_mode": False
}

SWAGGER_URL = '/swagger'
API_URL = '/static/swagger/swagger.yml'
SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Ansible Barn",
        'apisSorter': "alpha",
        'operationsSorter': "alpha",
        'layout': "BaseLayout"
    })

class BarnServer(Flask):
    def __init__(self, config_path, **kwargs):
        self.logger = None
        super(BarnServer, self).__init__(__name__,**kwargs)
        self.load_config_file(config_path)
        self._register_blueprints()

    def load_config_file(self,path):
        config = None
        if path.endswith(".ini") or path.endswith(".cfg"):
            config = BarnServer._load_ini_config_file(path)
        else:
            sys.exit("Could not load config file. Only allow .ini or .cfg files")

        #Verify MongoDB Configuration
        valid_config = True
        if "mongodb" in config:
            for required_setting in ["mongo_user","mongo_password","mongo_host","mongo_port","mongo_db"]:
                if not config.get("mongodb",{}).get(required_setting):
                    valid_config = False
                    self.logger.error("{} has no {} setting in the mongo section".format(path,required_setting))   
        else:
            valid_config = False
            self.logger.error("{} has no mongo settings".format(path))
        #Verify Barn Configuration
        if "barn" in config:
            if "barn_token_encryption_key" not in config.get("barn",{}):
                valid_config = False
                self.logger.error("{} has no {} in the barn section".format(path,"barn_token_encryption_key"))
        else:
            valid_config = False
            self.logger.error("{} has no barn settings".format(path))

        if valid_config:
            self.config.from_mapping(dict(
                BARN_CONFIG=config.get("barn"),
                TOKEN_ENCRYPTION_KEY=config.get("barn",{}).get("barn_token_encryption_key"),
                MONGODB_SETTINGS=dict(
                    db=config.get("mongodb",{}).get("mongo_db"),
                    host=config.get("mongodb",{}).get("mongo_host"),
                    username=config.get("mongodb",{}).get("mongo_user"),
                    password=config.get("mongodb",{}).get("mongo_password"),
                    authentication_source="admin"
            )))
        else:
            sys.exit("Invalid config file")

    def _db_init(self):
        if not User.objects(name=self.get_barn_config("barn_init_admin_user")).first():
            User(
                name=self.get_barn_config("barn_init_admin_user"),
                username=self.get_barn_config("barn_init_admin_user"),
                password=self.get_barn_config("barn_init_admin_password"),
                admin=True
            ).save()

    def get_barn_config(self, key):
        default_value = DEFAULT_BARN_CONFIG.get(key)
        self.config.get("BARN_CONFIG", {}).get(key,default_value)        

    @classmethod
    def _load_ini_config_file(cls,path):
        result = {}
        if os.path.isfile(path):
            config = configparser.ConfigParser()
            config.read(path)
            for section in config.sections():
                result[section] = {}
                for k, v in config.items(section):
                    if v and str(v).lower() in ["yes", "true", "on"]:
                        result[section][k] = True
                    elif v and str(v).lower() in ["no", "false", "off"]:
                        result[section][k] = False
                    elif v.isdigit():
                        result[section][k] = int(v)
                    elif v.replace('.', '', 1).isdigit() or v.replace(',', '', 1).isdigit():
                        result[section][k] = float(v.replace(',', '.', 1))
                    else:
                        result[section][k] = v
        return result

    def _register_blueprints(self):
        self.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
        self.register_blueprint(host_pages)
        self.register_blueprint(user_pages)
        self.register_blueprint(group_pages)
        self.register_blueprint(node_pages)
        self.register_blueprint(inventory_pages)
        self.register_blueprint(export_pages)
        self.register_blueprint(upload_pages)
        self.register_blueprint(login_pages)
        if self.config.get("BARN_CONFIG", {}).get("debug_mode", False):
            self.register_blueprint(debug_pages)
    

