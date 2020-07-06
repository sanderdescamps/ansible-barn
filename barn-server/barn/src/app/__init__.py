import os
from flask import Flask, request, jsonify, make_response
from flask_mongoengine import MongoEngine
import jwt
import configparser

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

def _load_config(path,section):
    """
        Load ini config file to dir
        When file doesn't exist, return empty directory
    """
    result = {}
    if os.path.isfile(path):
        config = configparser.ConfigParser()
        config.read(path)
        for k,v in config.items(section):
            result[k] = v
    return result
            

app = Flask(__name__)

cfg_path = os.path.join(os.getcwd(), "config/barn.cfg")
mongo_config = MONGO_DEFAULT_CONFIG.copy()
mongo_config.update(_load_config(cfg_path,"mongodb"))
app.config['MONGO_CONFIG'] = mongo_config

barn_config = BARN_DEFAULT_CONFIG.copy()
barn_config.update(_load_config(cfg_path,"barn"))
app.config['BARN_CONFIG'] = barn_config

app.config['TOKEN_ENCRYPTION_KEY'] = barn_config.get("barn_token_encryption_key")
app.config['MONGODB_SETTINGS'] = dict(
    db=mongo_config.get("mongo_db"),
    host=mongo_config.get("mongo_host"),
    username=mongo_config.get("mongo_user"),
    password=mongo_config.get("mongo_password"),
    authentication_source="admin"
)

db = MongoEngine(app)
