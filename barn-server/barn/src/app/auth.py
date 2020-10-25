from functools import wraps
import jwt
from werkzeug.security import check_password_hash
from flask import request, make_response, current_app
from app.models import User
from app.utils.formater import ResponseFormater


def authenticate(*roles):
    def require_token(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            resp = ResponseFormater()
            current_user = kwargs.get("current_user",None)
            

            token = request.headers.get('x-access-tokens', None)
            if current_user:
                pass
            elif token is not None and token != "":
                try:
                    data = dict(jwt.decode(
                        token, current_app.config["TOKEN_ENCRYPTION_KEY"]))
                    current_user = User.objects(
                        public_id=data.get("public_id")).first()
                except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.DecodeError):
                    return resp.authentication_error(msg='token is invalid').get_response()
                except jwt.exceptions.ExpiredSignatureError:
                    return resp.authentication_error(msg='token expired').get_response()
            elif request.authorization and request.authorization.username and request.authorization.password:
                auth = request.authorization
                current_user = User.objects(username=auth.username).first()
                if current_user is None:
                    return resp.authentication_error(msg='invalid user').get_response()
                if not check_password_hash(current_user.password_hash, auth.password):
                    return resp.authentication_error(msg='invalid username and password').get_response()
            elif "guest" in roles:
                kwargs["current_user"] = current_user
                return f(*args, **kwargs)

            if current_user is None:
                return resp.authentication_error(msg='Unauthorized request. Username/password or token required').get_response()
            missing_roles = current_user.missing_roles(roles)
            if len(missing_roles) > 1:
                return resp.authentication_error(msg='Not permited, missing roles (%s)' % (','.join(missing_roles))).get_response()
            kwargs["current_user"] = current_user
            return f(*args, **kwargs)

        return decorator
    return require_token
