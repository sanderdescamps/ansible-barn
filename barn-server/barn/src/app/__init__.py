import sys
import os
from flask import Flask, url_for, redirect
from flask.logging import create_logger
from flask_mongoengine import MongoEngine
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
from app.utils.config import ConfigLoader
from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s:  %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


app = Flask(__name__)
logger = create_logger(app)


# Swagger
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
    }
)
app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)

CFG_PATH = None
if len(sys.argv) > 1:
    CFG_PATH = sys.argv[1]
elif os.path.exists(os.path.join(os.getcwd(), "config/barn-server.cfg")):
    CFG_PATH = os.path.join(os.getcwd(), "config/barn-server.cfg")
elif os.path.exists("/etc/barn/barn-server.cfg"):
    CFG_PATH = "/etc/barn/barn-server.cfg"
else:
    logger.info("Can't find any config file")
    sys.exit("Can't find any config file")

logger.info("load config file: {}".format(CFG_PATH))
config = ConfigLoader(CFG_PATH).get_config()
app.config.from_mapping(config)


app.register_blueprint(host_pages)
app.register_blueprint(user_pages)
app.register_blueprint(group_pages)
app.register_blueprint(node_pages)
app.register_blueprint(inventory_pages)
app.register_blueprint(export_pages)
app.register_blueprint(upload_pages)
app.register_blueprint(login_pages)
if config.get("BARN_CONFIG", {}).get("debug_mode", False):
    app.register_blueprint(debug_pages)

db = MongoEngine(app)

if not User.objects(name=config.get("BARN_CONFIG", {}).get("barn_init_admin_user", "admin")).first():
    User(
        name=config.get("BARN_CONFIG", {}).get(
            "barn_init_admin_user", "admin"),
        username=config.get("BARN_CONFIG", {}).get(
            "barn_init_admin_user", "admin"),
        password=config.get("BARN_CONFIG", {}).get(
            "barn_init_admin_password", "admin"),
        admin=True
    ).save()
