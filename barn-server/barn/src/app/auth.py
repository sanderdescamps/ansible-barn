from functools import wraps
import jwt
from werkzeug.security import check_password_hash
from flask import request, jsonify, make_response
from app import app
from app.models import User


def authenticate(*roles):
    def require_token(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            current_user = None

            token = request.headers.get('x-access-tokens', None)
            if token is not None and token != "":
                try:
                    data = dict(jwt.decode(
                        token, app.config["TOKEN_ENCRYPTION_KEY"]))
                    current_user = User.objects(
                        public_id=data.get("public_id")).first()
                except jwt.exceptions.InvalidSignatureError:
                    # return make_response('token is invalid', 401)
                    return jsonify(error='token is invalid'), 401
                except jwt.exceptions.ExpiredSignatureError:
                    # return make_response('token expired', 401)
                    # abort(401,'token expired')
                    return jsonify(error='token expired'), 401
                except jwt.exceptions.DecodeError:
                    # abort(401,'token is invalid')
                    return jsonify(error='token is invalid'), 401
            elif request.authorization and request.authorization.username and request.authorization.password:
                auth = request.authorization
                current_user = User.objects(username=auth.username).first()
                if current_user is None:
                    return make_response(jsonify(error='invalid user'), 401, {
                        'WWW.Authentication': 'Basic realm: "login required"'
                    })
                if not check_password_hash(current_user.password_hash, auth.password):
                    return make_response(jsonify(error='invalid username and password'), 401, {
                        'WWW.Authentication': 'Basic realm: "login required"'
                    })
            elif "guest" in roles:
                return f(*args, current_user=None, **kwargs)
            else:
                return make_response(jsonify(error='Unauthorized request. Username/password or token required'), 401, {
                    'WWW.Authentication': 'Basic realm: "login required"'
                })

            missing_roles = current_user.missing_roles(roles)
            if len(missing_roles) > 1:
                return jsonify(
                    error='Not permited, missing roles (%s)' % (','.join(missing_roles))), 401

            return f(*args, current_user=current_user, **kwargs)

        return decorator
    return require_token
