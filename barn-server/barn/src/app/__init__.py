from flask import Flask, request, jsonify, make_response
from flask_mongoengine import MongoEngine
import jwt


app = Flask(__name__)

app.config['SECRET_KEY'] = "mlqdifjqmlsdfkjqmldkfjmoifjqmlsdjnm"
app.config['MONGODB_SETTINGS'] = dict(
    db="inventory",
    # host="192.168.56.3",
    # host="10.10.6.17",
    # host="192.168.122.59",
    # host="127.0.0.1",
    host="mongodb",
    username="admin-user",
    password="jfldmdpdeiehjkHGSthjjhDdfghhFdf",
    authentication_source="admin"
)

db = MongoEngine(app)
