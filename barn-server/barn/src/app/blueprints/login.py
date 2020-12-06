from flask import request, jsonify, Blueprint, redirect, url_for, Response
from flask_login import logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Email, Length, InputRequired


login_pages = Blueprint('login', __name__)

# @authenticate("guest")
# @login_pages.route('/login', methods=['GET', 'POST'])
# def login_user():
#     resp = ResponseFormater()
#     auth = request.authorization

#     if not auth or not auth.username or not auth.password:
#         return resp.authentication_error(msg='could not verify').get_response()

#     user = User.objects(username=auth.username).first()
#     if user is None:
#         return resp.authentication_error(msg='Could not login').get_response()
#     if check_password_hash(user.password_hash, auth.password):
#         token = jwt.encode({'public_id': user.public_id, 'exp': datetime.datetime.utcnow(
#         ) + datetime.timedelta(minutes=30)}, current_app.config['TOKEN_ENCRYPTION_KEY'])
#         return jsonify({'token': token.decode('UTF-8')})

#     return resp.authentication_error('Could not verify')

# @authenticate("guest")
# @login_pages.route('/login', methods=['GET', 'POST'])
# def login():
#     resp = ResponseFormater()
#     auth = request.authorization
#     token = request.headers.get('x-access-tokens', None)
#     current_user = None
#     if token is not None and token != "":
#         try:
#             data = dict(jwt.decode(token, current_app.config["TOKEN_ENCRYPTION_KEY"]))
#             current_user = User.objects(public_id=data.get("public_id")).first()
#         except (jwt.exceptions.InvalidSignatureError, jwt.exceptions.DecodeError):
#             return resp.authentication_error(msg='token is invalid').get_response()
#         except jwt.exceptions.ExpiredSignatureError:
#             return resp.authentication_error(msg='token expired').get_response()
#     elif auth and auth.username and auth.password:
#         current_user = User.objects(username=auth.username).first()
#         if current_user is None:
#             return resp.authentication_error(msg='invalid user').get_response()
#         if not check_password_hash(current_user.password_hash, auth.password):
#             return resp.authentication_error(msg='invalid username and password').get_response()
#     if current_user is not None:
#         print(dict(username=current_user.username, user_id=current_user.get_id()))
#         login_user(current_user)
#     else:
#         return Response('Login!', 401, {"WWW-Authenticate": 'Basic realm="Login!"'})
#     # next = request.args.get('next')
#     # print(next)
#     return jsonify(dict(msg="login successful"))

class RegForm(FlaskForm):
    email = StringField('email',  validators=[InputRequired(), Email(message='Invalid email'), Length(max=30)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=1, max=20)])

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
    
    # auth = request.authorization
    # token = request.headers.get('x-access-tokens', None)
    # next_page = request.args.get('next')
    # # if not is_safe_url(next):
    # #     return flask.abort(400)
    # if token is not None and token != "":
    #     data = dict(jwt.decode(token, current_app.config["TOKEN_ENCRYPTION_KEY"]))
    #     check_user = User.objects(public_id=data.get("public_id")).first()
    #     login_user(check_user)
    #     if next_page:
    #         redirect(next_page)
    #     return jsonify(dict(msg="login successful"))
    # elif auth and auth.username and auth.password:
    #     check_user = User.objects(username=auth.username).first()
    #     if check_password_hash(check_user.password_hash, auth.password):
    #         login_user(check_user)
    #         if next_page:
    #             redirect(url_for(next_page))
    #         return jsonify(dict(msg="login successful"))
    # return Response('Login!', 401, {"WWW-Authenticate": 'Basic realm="Login!"'})


@login_pages.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify(dict(msg="logout successful"))

@login_pages.route('/test', methods=['GET', 'POST'])
@login_required
def test():
    return jsonify(dict(msg="it works"))

@login_pages.route('/debug', methods=['GET', 'POST'])
def debug():

    return Response(dict(
        str()
    ))


