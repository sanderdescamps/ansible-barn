from logging.config import dictConfig
import os
import sys
import logging
from flask_mongoengine import MongoEngine
from waitress import serve
from app.BarnServer import BarnServer
from app.auth import login_manager, principals


dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '%(asctime)s [%(levelname)s] %(message)s',
        }
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            # 'stream': 'ext://flask.logging.wsgi_errors_stream',
            'stream': 'ext://sys.stderr',
            'formatter': 'default',
            'level': 'DEBUG'
        },
        "logfile":{
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'barn.log',
            'maxBytes': 1024,
            'backupCount': 3,
            'formatter': 'default',
            'level': 'DEBUG'
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['wsgi', 'logfile']
    }
})

CONFIG_PATHS = []
if len(sys.argv) > 1 and sys.argv[-1].endswith(".cfg"):
    CONFIG_PATHS += [sys.argv[1]]
if os.environ.get('BARN_CONFIG_FILE'):
    CONFIG_PATHS += os.environ.get('BARN_CONFIG_FILE')
CONFIG_PATHS += [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/barn-server.cfg"),
    "/etc/barn/barn-server.cfg"
]

logging.debug("Config paths: %s", ", ".join(CONFIG_PATHS))
cfg_path = next(
    (path for path in CONFIG_PATHS if os.path.exists(path)), None)
if cfg_path:
    logging.info("Use config file: %s", cfg_path)
else:
    sys.exit("Can't find any config file")
app = BarnServer(config_path=cfg_path)

db = MongoEngine()
db.init_app(app)
login_manager.init_app(app)
principals.init_app(app)
app.create_admin_user()


if __name__ == "__main__":
    serve(app, host='0.0.0.0', port=5000, threads=4)
    # app.run(host='0.0.0.0', port=5000, debug=True)
