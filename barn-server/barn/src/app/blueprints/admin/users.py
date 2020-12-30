import uuid

from flask import request, Blueprint
from flask_login import login_required
from werkzeug.security import generate_password_hash
from mongoengine.errors import NotUniqueError
from app.models import User
from app.utils.formater import ResponseFormater

user_pages = Blueprint('user', __name__)

@user_pages.route('/api/v1/admin/register', methods=['GET', 'POST'])
@login_required
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



# @user_pages.route('/api/v1/admin/users', methods=['GET'])
# @login_required
# def get_users():
#     resp = ResponseFormater()
#     users = User.objects()
#     resp.add_result(users.exclude("id"))
#     return resp.get_response()


@user_pages.route('/api/v1/admin/users', methods=['GET', 'POST'])
@login_required
def get_user():
    resp = ResponseFormater()
    user_kwargs = request.args if request.method == 'GET' else request.get_json(silent=True) or {}
    filtered_user_kwargs = {key: user_kwargs.get(key) for key in ["name", "username", "active", "public_id"] if key in user_kwargs}
    o_users = User.objects(**filtered_user_kwargs)
    if o_users:
        resp.add_result(o_users)
    else:
        resp.failed(msg="User(s) not found",status=404)
    return resp.get_response()


    
def get_user_list():
    pass

def add_user():
    pass

def delete_user():
    pass