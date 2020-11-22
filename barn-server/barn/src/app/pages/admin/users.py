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
@user_pages.route('/api/v1/admin/register', methods=['GET', 'POST'])
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


@authenticate("manageUsers")
@user_pages.route('/api/v1/admin/users', methods=['GET'])
def get_users():
    resp = ResponseFormater()
    users = User.objects()
    resp.add_result(users.exclude("id"))
    return resp.get_response()
