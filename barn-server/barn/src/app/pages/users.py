import uuid
import datetime
import jwt
from flask import request, jsonify, Blueprint, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine.errors import NotUniqueError
from app.auth import authenticate
from app.models import User
from flask import current_app

user_pages = Blueprint('user', __name__)


@user_pages.route('/register', methods=['GET', 'POST'])
def signup_user():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    try:
        new_user = User(public_id=str(uuid.uuid4()),
                        name=data['name'], username=data['username'],
                        password_hash=hashed_password, admin=False)
        new_user.save()
    except NotUniqueError:
        return jsonify(error='user already exists'), 400

    return jsonify({'message': 'registered successfully'})


@user_pages.route('/login', methods=['GET', 'POST'])
def login_user():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('could not verify', 401, {
            'WWW.Authentication': 'Basic realm: "login required"'
        })

    user = User.objects(username=auth.username).first()
    if user is None:
        return make_response('Could not login', 401, {
            'WWW.Authentication': 'Basic realm: "login required"'
        })
    if check_password_hash(user.password_hash, auth.password):
        token = jwt.encode({'public_id': user.public_id, 'exp': datetime.datetime.utcnow(
        ) + datetime.timedelta(minutes=30)}, current_app.config['TOKEN_ENCRYPTION_KEY'])
        print("token: %s" % token.decode('UTF-8'))
        return jsonify({'token': token.decode('UTF-8')})

    return make_response('could not verify', 401, {
        'WWW.Authentication': 'Basic realm: "login required"'
    })


@user_pages.route('/users', methods=['GET'])
def get_all_users():
    users = User.objects()
    return jsonify({"result": users.exclude("id")})
