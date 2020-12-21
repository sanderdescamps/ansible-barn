from flask import request, jsonify, Blueprint, redirect, url_for, Response, abort
from flask_login import logout_user, login_required, current_user
from app.auth import admin_permission
import logging



login_pages = Blueprint('login', __name__)


@login_pages.route('/login', methods=['GET', 'POST'])
def login():
    auth = request.authorization
    token = request.headers.get('x-access-tokens', None)
    next_page = request.args.get('next')
    if current_user.is_authenticated:
        if next_page:
            return redirect(url_for(next_page))
        return jsonify(dict(msg="login successful"))
    elif (auth and auth.username and auth.password) or (token is not None and token != ""):
        abort(401, description="Authentication failed")
    else:
        abort(401, description="Authentication required")

@login_pages.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify(dict(msg="logout")), 401



