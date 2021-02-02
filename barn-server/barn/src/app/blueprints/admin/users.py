import uuid
from flask import request, Blueprint, abort
from flask_login import login_required
from werkzeug.security import check_password_hash, generate_password_hash
from mongoengine.errors import NotUniqueError, DoesNotExist
from app.models import User
from app.utils.formater import ResponseFormater
from app.utils import list_parser, merge_args_data, generate_password, boolean_parser
from app.auth import admin_permission


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


@user_pages.route('/api/v1/admin/users', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def get_user():
    resp = ResponseFormater()
    user_kwargs = request.args if request.method == 'GET' else request.get_json(
        silent=True) or {}
    filtered_user_kwargs = {key: user_kwargs.get(key) for key in [
        "name", "username", "active", "public_id"] if key in user_kwargs}
    o_users = User.objects(**filtered_user_kwargs)
    if o_users:
        resp.add_result(o_users)
    else:
        resp.failed(msg="User(s) not found", status=404)
    return resp.get_response()


@user_pages.route('/api/v1/admin/users', defaults={'action': "present"}, methods=['PUT'])
@user_pages.route('/api/v1/admin/users/<string:action>', methods=['PUT'])
@login_required
@admin_permission.require(http_exception=403)
def put_user(action="present"):

    resp = ResponseFormater()
    request_args = request.get_json(silent=True)
    if request_args is None:
        abort(400, description="Bad Request")

    username = request_args.get("username",None)
    if not username:
        resp.failed("{} not defined".format("username"))
        return resp.get_response()

    o_user = User.objects(username=username).first()
    if not o_user:
        if action == "present" or action == "add":
            try:
                allowed_args = ["username", "name", "active", "roles", "password", "password_hash"]
                user_kwargs = {key:value for key,value in request_args.items() if key in allowed_args}
                resp += _add_user(**user_kwargs)
            except NotUniqueError:
                resp.failed("User already exist", status=400)
        else:
            resp.failed("User does not exist. Set action to 'add' or 'present' if you want to create the user", status=400)
    else:
        if action == "update" or action == "present":
            allowed_args = ["username", "name", "active", "roles", "password", "password_hash"]
            user_kwargs = {key:value for key,value in request_args.items() if key in allowed_args}
            resp += _modify_user(**user_kwargs)
        elif action == "add":
            resp.failed("User already exist", status=400)
        elif action == "passwd":
            new_password = request_args.get("password")
            if new_password:
                resp += _modify_user(username=username, password=new_password)
            else: 
                resp.failed("password not defined", status=400)

    #create user
    if action == "present":
        pass

    return resp.get_response()

def _add_user(**kwargs):
    resp = ResponseFormater()
    user_kwargs = kwargs.copy()

    if "password" not in user_kwargs and "password_hash" not in user_kwargs:
        user_kwargs["password"] = generate_password()
        resp.add_message("Generate random password for {}".format(user_kwargs.get("username","unknown user")))

    if user_kwargs.get("roles") is not None:
        user_kwargs["roles"] = list_parser(user_kwargs.get("roles"))

    try:
        o_user = User(**user_kwargs)
        o_user.save()
        resp.add_message("User created")
        resp.changed()
    except NotUniqueError:
        raise NotUniqueError
    return resp
    
def _modify_user(**user_kwargs):
    resp = ResponseFormater()

    username = user_kwargs.get("username")
    if username is None:
        resp.failed("{} not defined".format(username))
        return resp
    
    o_user = User.objects(username=username).first()
    o_user_hash = hash(o_user)
    if not o_user: 
        resp.failed("{} user not found".format(username))
        return resp

    if "active" in user_kwargs and user_kwargs.get("active") != o_user.active:
        o_user.active = boolean_parser(user_kwargs.get("active"))

    if "name" in user_kwargs and user_kwargs.get("name") != o_user.active:
        o_user.name = user_kwargs.get("name")
        
    if "password_hash" in user_kwargs and user_kwargs.get("password_hash") != o_user.password_hash:
        password_hash = user_kwargs.get("password_hash")
        if password_hash.startswith("sha256$"):
            o_user.password_hash = password_hash
        else:
            resp.add_message("invalid password hash")
    elif "password" in user_kwargs:
        password = user_kwargs.pop("password").strip()
        if not check_password_hash(o_user.password_hash, password):
            o_user.password_hash = generate_password_hash(password, method='sha256')


    if user_kwargs.get("roles") is not None:
        o_user.roles = list(set(o_user.roles + list_parser(user_kwargs.get("roles"))))

    if o_user_hash != hash(o_user):
        o_user.save()
        resp.add_message("User modified")
        resp.changed()

    return resp


@user_pages.route('/api/v1/admin/users', methods=['DELETE'])
@login_required
@admin_permission.require(http_exception=403)
def delete_user():
    resp = ResponseFormater()
    request_args = merge_args_data(request.args, request.get_json(silent=True))
    user_kwargs = {key: request_args.get(key) for key in [
        "name", "username", "public_id"] if key in request_args}
    o_users = User.objects(**user_kwargs)
    if o_users:
        o_users.delete()
        resp.changed()
        resp.add_message("User(s) removed")
    else:
        resp.failed(msg="User(s) not found", status=404)
    return resp.get_response()

