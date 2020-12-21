import os
import sys
import random
import string
import configparser
import logging
from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint
from app.blueprints.admin.users import user_pages
from app.blueprints.admin.export import export_pages
from app.blueprints.inventory.hosts import host_pages
from app.blueprints.inventory.groups import group_pages
from app.blueprints.inventory.nodes import node_pages
from app.blueprints.inventory_export import inventory_pages
from app.blueprints.debug import debug_pages
from app.blueprints.upload import upload_pages
from app.blueprints.login import login_pages
from app.blueprints.error import handle_authentication_failed, handle_bad_request, handle_internal_server_error, handle_mongodb_unreachable, pokemon_exception_handler
from werkzeug.exceptions import NotFound, Unauthorized, InternalServerError
from pymongo.errors import ServerSelectionTimeoutError
from app.models import User


DEFAULT_BARN_CONFIG = {
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
        super().__init__(__name__, **kwargs)
        self.load_config_file(config_path)
        self._register_blueprints()
        self._register_error_handlers()

        # self.db = MongoEngine()
        # self.db.init_app(self)
        # self.user_datastore = MongoEngineUserDatastore(self.db, User, Role)
        # self.security = Security(self, self.user_datastore)

    def load_config_file(self, path):
        config = None
        if path.endswith(".ini") or path.endswith(".cfg"):
            config = BarnServer._load_ini_config_file(path)
        else:
            sys.exit("Could not load config file. Only allow .ini or .cfg files")

        # Session key
        default_random_key = ''.join(random.choice(
            string.ascii_letters + string.digits) for i in range(32))
        self.secret_key = config.get("barn", {}).get(
            "barn_session_key", default_random_key)

        # Verify MongoDB Configuration
        valid_config = True
        if "mongodb" in config:
            for required_setting in ["mongo_user", "mongo_password", "mongo_host", "mongo_port", "mongo_db"]:
                if not config.get("mongodb", {}).get(required_setting):
                    valid_config = False
                    logging.getLogger().error(
                        "%s has no %s setting in the mongo section", path, required_setting)
        else:
            valid_config = False
            logging.getLogger().error("%s has no mongo settings", path)
        # Verify Barn Configuration
        if "barn" in config:
            if "barn_token_encryption_key" not in config.get("barn", {}):
                valid_config = False
                logging.getLogger().error("%s has no %s in the barn section",
                                          path, "barn_token_encryption_key")
        else:
            valid_config = False
            logging.getLogger().error("%s has no barn settings", path)

        if valid_config:
            self.config.from_mapping(dict(
                BARN_CONFIG=config.get("barn"),
                TOKEN_ENCRYPTION_KEY=config.get("barn", {}).get(
                    "barn_token_encryption_key"),
                MONGODB_SETTINGS=dict(
                    db=config.get("mongodb", {}).get("mongo_db"),
                    host=config.get("mongodb", {}).get("mongo_host"),
                    username=config.get("mongodb", {}).get("mongo_user"),
                    password=config.get("mongodb", {}).get("mongo_password"),
                    authentication_source="admin"
                )))
        else:
            sys.exit("Invalid config file")

    def create_admin_user(self):
        """
            Create admin user if not exist
        """
        if not User.objects(username=self.get_barn_config("barn_init_admin_user")).first():
            User(
                name=self.get_barn_config("barn_init_admin_user"),
                username=self.get_barn_config("barn_init_admin_user"),
                password=self.get_barn_config("barn_init_admin_password"),
                admin=True
            ).save()
            logging.info("Create admin user")

    def get_barn_config(self, key):
        default_value = DEFAULT_BARN_CONFIG.get(key)
        return self.config.get("BARN_CONFIG", {}).get(key, default_value)

    @classmethod
    def _load_ini_config_file(cls, path):
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

    def _register_error_handlers(self):
        self.register_error_handler(NotFound, handle_bad_request)
        self.register_error_handler(Unauthorized, handle_authentication_failed)
        self.register_error_handler(
            InternalServerError, handle_internal_server_error)
        self.register_error_handler(
            ServerSelectionTimeoutError, handle_mongodb_unreachable)
        self.register_error_handler(Exception, pokemon_exception_handler)
