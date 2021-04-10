import jwt
import datetime
import logging
import re
import uuid
from flask import request, abort, current_app, jsonify
from flask_smorest import Blueprint
from flask_login import login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from mongoengine.errors import NotUniqueError, DoesNotExist
from app.models import User
from app.utils.formater import ResponseBuilder
from app.utils import list_parser, merge_args_data, generate_password, boolean_parser
from app.auth import admin_permission
from app.utils.schemas import RegisterUserArgsSchema, UserPasswdSchema, UserPutQueryArgsSchema, UserQueryArgsSchema

user_pages = Blueprint('user', __name__)


@user_pages.route('/api/v1/admin/register', methods=['GET'])
@user_pages.arguments(RegisterUserArgsSchema, location='query', as_kwargs=True)
@user_pages.doc(deprecated=True)
@login_required
def get_signup_user(**kwargs):
    """Register new user"""
    return _signup_user(**kwargs)

@user_pages.route('/api/v1/admin/register', methods=['POST'])
@user_pages.arguments(RegisterUserArgsSchema, location='query', as_kwargs=True)
@user_pages.arguments(RegisterUserArgsSchema, location='json', as_kwargs=True)
@user_pages.doc(deprecated=True)
@login_required
def post_signup_user(**kwargs):
    """Register new user"""
    return _signup_user(**kwargs)

def _signup_user(**kwargs):
    resp = ResponseBuilder()
    hashed_password = kwargs.get("password_hash") or generate_password_hash(kwargs.get('password'), method='sha256')
    try:
        new_user = User(public_id=str(uuid.uuid4()),
                        name=kwargs.get('name'), username=kwargs.get('username'),
                        password_hash=hashed_password, admin=False)
        new_user.save()
    except NotUniqueError:
        return resp.failed(msg='user already exists').build()

    return resp.succeed(msg='registered successfully').build()

@user_pages.route('/api/v1/admin/users', methods=['GET'])
@user_pages.arguments(UserQueryArgsSchema, location='query', as_kwargs=True)
@login_required
@admin_permission.require(http_exception=403)
def get_user(**kwargs):
    """List of users

    """
    return _get_user(**kwargs)

@user_pages.route('/api/v1/admin/users', methods=['POST'])
@user_pages.arguments(UserQueryArgsSchema, location='query', as_kwargs=True)
@user_pages.arguments(UserQueryArgsSchema, location='json', as_kwargs=True)
@login_required
@admin_permission.require(http_exception=403)
def post_user(**kwargs):
    """List of users

    """    
    return _get_user(**kwargs)

def _get_user(**kwargs):
    resp = ResponseBuilder()
    query_args = {}
    if "name" in kwargs:
        query_args["name"] = re.compile(r'.*{}.*'.format(kwargs.get("name")), re.IGNORECASE)
    
    for key in ["username", "active", "public_id"]:
        if key in kwargs:
            query_args[key] = kwargs.get(key)

    o_users = User.objects(**query_args)
    if o_users:
        resp.add_result(o_users)
    else:
        resp.failed(msg="User(s) not found", status=404)
    return resp.build()


@user_pages.route('/api/v1/admin/users', methods=['PUT'])
@user_pages.arguments(UserPutQueryArgsSchema, location='json', as_kwargs=True)
@login_required
@admin_permission.require(http_exception=403)
def put_user_short(**kwargs):
    put_user(**kwargs)

@user_pages.route('/api/v1/admin/users/<string:action>', methods=['PUT'])
@user_pages.arguments(UserPutQueryArgsSchema, location='json', as_kwargs=True)
@login_required
@admin_permission.require(http_exception=403)
def put_user(action="present", **kwargs):
    resp = ResponseBuilder()

    username = kwargs.get("username",None)
    action = action or kwargs.get("action")

    o_user = User.objects(username=username).first()
    if not o_user:
        if action == "present" or action == "add":
            try:
                allowed_args = ["admin","username", "name", "active", "roles", "password", "password_hash"]
                user_kwargs = {key:value for key,value in kwargs.items() if key in allowed_args}
                resp += _add_user(**user_kwargs)
            except NotUniqueError:
                resp.failed("User already exist", status=400)
        else:
            resp.failed("User does not exist. Set action to 'add' or 'present' if you want to create the user", status=400)
    else:
        if action == "update" or action == "present":
            allowed_args = ["username", "name", "active", "roles", "password", "password_hash"]
            user_kwargs = {key:value for key,value in kwargs.items() if key in allowed_args}
            resp += _modify_user(**user_kwargs)
        elif action == "add":
            resp.failed("User already exist", status=400)


    #create user
    if action == "present":
        pass

    return resp.build()

@user_pages.route('/api/v1/admin/users/passwd', methods=['PUT'])
@user_pages.arguments(UserPasswdSchema, location='json', as_kwargs=True)
@login_required
def put_user_passwd(**kwargs):
    """Change user password

    """
    resp = ResponseBuilder()
    username = kwargs.get("username")
    o_current_user = User.objects(public_id=current_user.get_id()).first()
    if not (username == o_current_user.username or o_current_user.has_role("admin")):
        return resp.failed("Permission denied").build()

    o_user = User.objects(username=username).first()
    if not o_user:
        return resp.failed("User does not exist").build()

    if "password_hash" in kwargs:
        resp += _modify_user(username=username, password_hash=kwargs.get("password_hash") )
    elif "password" in kwargs:
        resp += _modify_user(username=username, password=kwargs.get("password") )
    else:
        return resp.bad_request("Password not defined").build()
    return resp.build()



def _add_user(**kwargs):
    resp = ResponseBuilder()
    user_kwargs = kwargs.copy()

    if "password" not in user_kwargs and "password_hash" not in user_kwargs:
        user_kwargs["password"] = generate_password()
        resp.log("Generate random password for {}".format(user_kwargs.get("username","unknown user")))

    if user_kwargs.get("roles") is not None:
        user_kwargs["roles"] = list_parser(user_kwargs.get("roles"))

    try:
        o_user = User(**user_kwargs)
        o_user.save()
        resp.log("User created")
        resp.changed()
    except NotUniqueError:
        raise NotUniqueError
    return resp
    
def _modify_user(**user_kwargs):
    resp = ResponseBuilder()

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
        if not password_hash.startswith("sha256$"):
            resp.log("invalid password hash")
        elif o_user.password_hash != password_hash:
            o_user.password_hash = password_hash
            resp.log("Password updated")
            resp.changed()
    elif "password" in user_kwargs:
        password = user_kwargs.pop("password").strip()
        if not check_password_hash(o_user.password_hash, password):
            o_user.password_hash = generate_password_hash(password, method='sha256')


    if user_kwargs.get("roles") is not None:
        o_user.roles = list(set(o_user.roles + list_parser(user_kwargs.get("roles"))))

    if o_user_hash != hash(o_user):
        o_user.save()
        resp.log("User modified")
        resp.changed()

    return resp


@user_pages.route('/api/v1/admin/users', methods=['DELETE'])
@login_required
@admin_permission.require(http_exception=403)
def delete_user():
    resp = ResponseBuilder()
    request_args = merge_args_data(request.args, request.get_json(silent=True))
    user_kwargs = {key: request_args.get(key) for key in [
        "name", "username", "public_id"] if key in request_args}
    o_users = User.objects(**user_kwargs)
    if o_users:
        o_users.delete()
        resp.changed()
        resp.log("User(s) removed")
    else:
        resp.failed(msg="User(s) not found", status=404)
    return resp.build()

@user_pages.route('/token', methods=['GET', 'POST'])
@user_pages.route('/api/v1/users/token', methods=['GET', 'POST'])
@login_required
def login_user():
    user = current_user
    token = jwt.encode({'public_id': user.public_id, 'exp': datetime.datetime.utcnow(
        ) + datetime.timedelta(minutes=30)}, current_app.config['TOKEN_ENCRYPTION_KEY'])
    return jsonify({'token': token})