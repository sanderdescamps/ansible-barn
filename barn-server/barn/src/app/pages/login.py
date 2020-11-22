import datetime
import jwt
from flask import request, jsonify, Blueprint, current_app
from werkzeug.security import check_password_hash
from app.auth import authenticate
from app.models import User
from app.utils.formater import ResponseFormater

login_pages = Blueprint('login', __name__)

@authenticate("guest")
@login_pages.route('/login', methods=['GET', 'POST'])
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