# from functools import wraps
import logging
import jwt
from werkzeug.security import check_password_hash
from flask import request, current_app, redirect, url_for, abort
from flask_login import LoginManager
from flask_principal import Principal, identity_changed, identity_loaded, Identity, RoleNeed, Permission
from app.models import User

# def authenticate(*roles):
#     def require_token(f):
#         @wraps(f)
#         def decorator(*args, **kwargs):
#             resp = ResponseFormater()
#             current_user = kwargs.get("current_user", None)

#             token = request.headers.get('x-access-tokens', None)
#             if current_user:
#                 pass
#             elif token is not None and token != "":
#                 try:
#                     data = dict(jwt.decode(
#                         token, current_app.config["TOKEN_ENCRYPTION_KEY"]))
#                     current_user = User.objects(
#                         public_id=data.get("public_id")).first()
#                 except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.DecodeError):
#                     return resp.authentication_error(msg='token is invalid').get_response()
#                 except jwt.exceptions.ExpiredSignatureError:
#                     return resp.authentication_error(msg='token expired').get_response()
#             elif request.authorization and request.authorization.username and request.authorization.password:
#                 auth = request.authorization
#                 current_user = User.objects(username=auth.username).first()
#                 if current_user is None:
#                     return resp.authentication_error(msg='invalid user').get_response()
#                 if not check_password_hash(current_user.password_hash, auth.password):
#                     return resp.authentication_error(msg='invalid username and password').get_response()
#             elif "guest" in roles:
#                 kwargs["current_user"] = current_user
#                 return f(*args, **kwargs)

#             if current_user is None:
#                 return resp.authentication_error(msg='Unauthorized request. Username/password or token required').get_response()
#             missing_roles = current_user.missing_roles(roles)
#             if len(missing_roles) > 1:
#                 return resp.authentication_error(msg='Not permited, missing roles (%s)' % (','.join(missing_roles))).get_response()
#             kwargs["current_user"] = current_user
#             return f(*args, **kwargs)

#         return decorator
#     return require_token

login_manager = LoginManager()
login_manager.login_view = "/login"

principals = Principal()
admin_permission = Permission(RoleNeed('admin'))


@login_manager.user_loader
def load_user(user_id):
    return User.objects(public_id=user_id).first()

@login_manager.request_loader
def load_user_from_request(l_request):
    auth = l_request.authorization
    token = l_request.headers.get('x-access-tokens', None)

    if token is not None and token != "":
        try:
            data = dict(jwt.decode(token, current_app.config["TOKEN_ENCRYPTION_KEY"]))
            check_user = User.objects(public_id=data.get("public_id")).first()
            if check_user:
                identity_changed.send(current_app._get_current_object(), identity=Identity(check_user.public_id))
                logging.getLogger().info("Auth: User %s logged in with token", check_user.username)
                return check_user
        except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.DecodeError):
            logging.getLogger().info("Auth: Invalid token: {}".format(token))
        except jwt.exceptions.ExpiredSignatureError:
            logging.getLogger().info("Auth: Token expired: {}".format(token))

    elif auth and auth.username and auth.password:
        check_user = User.objects(username=auth.username).first()
        if check_password_hash(check_user.password_hash, auth.password):
            identity_changed.send(current_app._get_current_object(), identity=Identity(check_user.public_id))
            logging.getLogger().info("Auth: User %s logged in", check_user.username)
            return check_user
        else:
            logging.getLogger().info("Auth: User %s failed to login", check_user.username)

    return None

@login_manager.unauthorized_handler
def unauthorized():
    auth = request.authorization
    token = request.headers.get('x-access-tokens', None)
    if not ((auth and auth.username and auth.password) or token):
        if request.user_agent.browser:
            schema = request.headers.get("X-Forwarded-Proto")
            host = request.headers.get("X-Forwarded-Host")
            port = request.headers.get("X-Forwarded-Port")
            if schema and port and host:
                return redirect("{}://{}:{}{}".format(schema, host, port, url_for("login.login", next=request.endpoint)))
            else:
                return redirect(url_for("login.login", next=request.endpoint))
        else:
            abort(401, description="Authentication required")
    else:
        abort(401, description="Authentication failed")

@identity_loaded.connect
def on_identity_loaded(sender, identity):
    o_user = User.objects(public_id=identity.id).first()
    if o_user:
        for role in o_user.get_roles():
            identity.provides.add(role)
