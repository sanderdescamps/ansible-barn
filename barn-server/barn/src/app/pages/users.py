import uuid
import datetime
import jwt
from flask import request, jsonify, Blueprint, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from mongoengine.errors import NotUniqueError
from app.auth import authenticate
from app.models import User
from app.utils.formater import ResponseFormater

user_pages = Blueprint('user', __name__)

@authenticate("createUser")
@user_pages.route('/register', methods=['GET', 'POST'])
def signup_user():
    resp = ResponseFormater()
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    try:
        new_user = User(public_id=str(uuid.uuid4()),
                        name=data['name'], username=data['username'],
                        password_hash=hashed_password, admin=False)
        new_user.save()
    except NotUniqueError:
        return resp.failed(msg='user already exists').get_response()

    return resp.succeed(msg='registered successfully').get_response()

@authenticate("guest")
@user_pages.route('/login', methods=['GET', 'POST'])
def login_user():
    resp = ResponseFormater()
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return resp.authentication_error(msg='could not verify').get_response()

    user = User.objects(username=auth.username).first()
    if user is None:
        return resp.authentication_error(msg='Could not login').get_response()
    if check_password_hash(user.password_hash, auth.password):
        token = jwt.encode({'public_id': user.public_id, 'exp': datetime.datetime.utcnow(
        ) + datetime.timedelta(minutes=30)}, current_app.config['TOKEN_ENCRYPTION_KEY'])
        return jsonify({'token': token.decode('UTF-8')})

    return resp.authentication_error('Could not verify')

@authenticate("manageUsers")
@user_pages.route('/users', methods=['GET'])
def get_all_users():
    resp = ResponseFormater()
    users = User.objects()
    resp.add_result(users.exclude("id"))
    return resp.get_response()
