from flask import request, jsonify, Blueprint, redirect, url_for, Response
from flask_login import logout_user, login_required, current_user



login_pages = Blueprint('login', __name__)


@login_pages.route('/login', methods=['GET', 'POST'])
def login():
    print("enter login method")
    auth = request.authorization
    token = request.headers.get('x-access-tokens', None)
    next_page = request.args.get('next')
    if current_user.is_authenticated:
        if next_page:
            return redirect(url_for(next_page))
        return jsonify(dict(msg="login successful"))
    elif (auth and auth.username and auth.password) or (token is not None and token != ""):
        return jsonify(dict(msg="login failed"))
    else:
        return Response('Login!', 401, {"WWW-Authenticate": 'Basic realm="Login!"'})


@login_pages.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify(dict(msg="logout successful"))


@login_pages.route('/test', methods=['GET', 'POST'])
@login_required
def test():
    return jsonify(dict(msg="it works"))
