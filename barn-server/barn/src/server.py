import os
import sys
from app.BarnServer import BarnServer
from flask_mongoengine import MongoEngine
from waitress import serve

# if __name__ == '__main__':
#     serve(app, host='0.0.0.0', port=5000,threads=4)
#     # app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

CONFIG_PATHS = [
    sys.argv[1],
    os.path.join(os.getcwd(), "config/barn-server.cfg"),
    "/etc/barn/barn-server.cfg"
]

if __name__ == "__main__":
    cfg_path = next((path for path in CONFIG_PATHS if os.path.exists(path)), None)
    if not cfg_path:
        sys.exit("Can't find any config file")
    app = BarnServer(config_path=cfg_path)
    MongoEngine().init_app(app)
    serve(app, host='0.0.0.0', port=5000,threads=4)
