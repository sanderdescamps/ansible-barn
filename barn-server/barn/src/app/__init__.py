import sys
import os
from flask import Flask, url_for, redirect
from flask_mongoengine import MongoEngine
from flask_swagger_ui import get_swaggerui_blueprint
from app.config import ConfigLoader
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


app = Flask(__name__)


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

cfg_path = None
if len(sys.argv) > 1:
    cfg_path = sys.argv[1]
elif os.path.exists(os.path.join(os.getcwd(), "config/barn-server.cfg")):
    cfg_path = os.path.join(os.getcwd(), "config/barn-server.cfg")
elif os.path.exists("/etc/barn/barn-server.cfg"):
    cfg_path = "/etc/barn/barn-server.cfg"
else:
    print("Can't load config file")
    sys.exit("Couldn't find config file")

config = ConfigLoader(cfg_path)
app.config['BARN_CONFIG'] = config
app.config['TOKEN_ENCRYPTION_KEY'] = config.get_barn_config().get(
    "barn_token_encryption_key")
app.config['MONGODB_SETTINGS'] = config.get_mongo_settings()

app.register_blueprint(host_pages)
app.register_blueprint(user_pages)
app.register_blueprint(group_pages)
app.register_blueprint(node_pages)
app.register_blueprint(inventory_pages)
app.register_blueprint(export_pages)
app.register_blueprint(upload_pages)
app.register_blueprint(login_pages)
if config.get_barn_config().get("debug_mode", False):
    app.register_blueprint(debug_pages)

db = MongoEngine(app)

if not User.objects(name=config.get_barn_config().get("barn_init_admin_user", "admin")).first():
    User(
        name=config.get_barn_config().get("barn_init_admin_user", "admin"),
        username=config.get_barn_config().get("barn_init_admin_user", "admin"),
        password=config.get_barn_config().get("barn_init_admin_password", "admin"),
        admin=True
    ).save()
