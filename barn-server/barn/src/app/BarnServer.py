import os
import sys
import random
import string
import configparser
import logging
from flask import Flask
from flask_smorest import Api
from flask_smorest.spec import ResponseReferencesPlugin
from app.blueprints.admin.users import user_pages
from app.blueprints.admin.export import export_pages
from app.blueprints.admin.data_import import import_pages
from app.blueprints.inventory.hosts import host_pages
from app.blueprints.inventory.groups import group_pages
from app.blueprints.inventory.nodes import node_pages
from app.blueprints.inventory_export import inventory_pages
from app.blueprints.debug import debug_pages
from app.blueprints.views import views
from app.blueprints.login import login_pages
from app.blueprints.error import handle_authentication_failed, handle_bad_request, handle_internal_server_error, handle_mongodb_unreachable, pokemon_exception_handler, handle_not_found, handle_forbidden, handle_unprocessable_entity
from werkzeug.exceptions import Forbidden, NotFound, Unauthorized, InternalServerError, BadRequest
from pymongo.errors import ServerSelectionTimeoutError
from app.models import User
from app.utils.schemas import BarnError

BARN_VERSION="1.1.0"

DEFAULT_BARN_CONFIG = {
    "barn_init_admin_user": "admin",
    "barn_init_admin_password": "admin",
    "debug_mode": False
}

# SWAGGER_URL = '/swagger'
# API_URL = '/static/swagger/swagger.yml'
# SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
#     SWAGGER_URL,
#     API_URL,
#     config={
#         'app_name': "Ansible Barn",
#         'apisSorter': "alpha",
#         'operationsSorter': "alpha",
#         'layout': "BaseLayout"
#     })

#Swagger
from flask_smorest import Api, Blueprint, abort


class BarnServer(Flask):
    def __init__(self, config_path, **kwargs):
        super().__init__(__name__, **kwargs)
        self.load_config_file(config_path)
        self.spec = Api(self, spec_kwargs=dict(
            response_plugin=ResponseReferencesPlugin(BarnError),
            security = [{"bearerAuth": []}],
            components = { 
                "securitySchemes": {
                    "basicAuth": {
                        "type": "http",
                        "scheme": "basic"
                    }
                },
                # "bearerAuth": {
                #         "type":"http",
                #         "scheme": "bearer",
                #         "bearerFormat": "JWT"
                # }
            }))
        

        # self.spec.DEFAULT_ERROR_RESPONSE_NAME = None
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

        # MongoDB Configuration
        valid_config = True
        mongodb_config = config.get("mongodb")
        if mongodb_config:
            required_setting = ["mongo_user", "mongo_password", "mongo_host", "mongo_port", "mongo_db"]
            missing_settings = [s for s in required_setting if s not in mongodb_config]
            if len(missing_settings) > 0:
                logging.getLogger().error("Missing settings [%s] in mongo section of %s",",".join(missing_settings), path)
            else:
                self.config.from_mapping(dict(
                    MONGODB_SETTINGS=dict(
                        db=mongodb_config.get("mongo_db"),
                        host=mongodb_config.get("mongo_host"),
                        username=mongodb_config.get("mongo_user"),
                        password=mongodb_config.get("mongo_password"),
                        authentication_source="admin"
                    )))
        else:
            sys.exit("Invalid config file")
        
        # Barn Configuration
        barn_config = config.get("barn")
        if barn_config:
            if "barn_token_encryption_key" not in barn_config:
                logging.getLogger().error("%s has no %s in the barn section",
                                          path, "barn_token_encryption_key")
            else:
                self.config.from_mapping(dict(
                    BARN_CONFIG=barn_config,
                    TOKEN_ENCRYPTION_KEY=barn_config.get("barn_token_encryption_key"))
                    )    
        else:
            logging.getLogger().error("%s has no barn settings", path)

        # OpenAPI Configuration (swagger)
        openapi_config = config.get("openapi", {})
        self.config.from_mapping(dict(
            API_TITLE="Barn",
            API_VERSION = BARN_VERSION,
            OPENAPI_VERSION = openapi_config.get("version",'3.0.2'),
            OPENAPI_URL_PREFIX = openapi_config.get("url_prefix",'/'),
            OPENAPI_JSON_PATH = openapi_config.get("json_path",'openapi.json'),
            OPENAPI_SWAGGER_UI_PATH = openapi_config.get("swagger_ui_path",'swagger-ui'),
            OPENAPI_SWAGGER_UI_URL = openapi_config.get("swagger_ui_url",'https://cdn.jsdelivr.net/npm/swagger-ui-dist/')
            ))

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
        self.register_blueprint(host_pages)
        self.register_blueprint(user_pages)
        self.register_blueprint(group_pages)
        self.register_blueprint(node_pages)
        self.register_blueprint(inventory_pages)
        self.register_blueprint(export_pages)
        self.register_blueprint(import_pages)
        self.register_blueprint(views)
        self.register_blueprint(login_pages)
        if self.config.get("BARN_CONFIG", {}).get("debug_mode", False):
            self.register_blueprint(debug_pages)
        
        self.spec.register_blueprint(host_pages)
        self.spec.register_blueprint(user_pages)
        self.spec.register_blueprint(group_pages)
        self.spec.register_blueprint(node_pages)
        self.spec.register_blueprint(inventory_pages)
        self.spec.register_blueprint(export_pages)
        self.spec.register_blueprint(import_pages)
        self.spec.register_blueprint(views)
        self.spec.register_blueprint(login_pages)
        if self.config.get("BARN_CONFIG", {}).get("debug_mode", False):
            self.spec.register_blueprint(debug_pages)

    def _register_error_handlers(self):
        self.register_error_handler(NotFound, handle_not_found)
        self.register_error_handler(Unauthorized, handle_authentication_failed)
        self.register_error_handler(BadRequest, handle_bad_request)
        self.register_error_handler(400, handle_bad_request)
        self.register_error_handler(
            InternalServerError, handle_internal_server_error)
        self.register_error_handler(422,handle_unprocessable_entity)
        self.register_error_handler(Forbidden, handle_forbidden)
        self.register_error_handler(
            ServerSelectionTimeoutError, handle_mongodb_unreachable)
        self.register_error_handler(Exception, pokemon_exception_handler)
