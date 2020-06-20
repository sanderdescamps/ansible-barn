from flask import request, jsonify, make_response
from flask_mongoengine import MongoEngine
from mongoengine import StringField, IntField, BooleanField
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import jwt
import datetime
from functools import wraps

from app import app
from app.models import User, Host, Group

def authenticate(roles=None):
    def require_token(f):
        @wraps(f)
        def decorator(*args, **kwargs):

            token = None

            if 'x-access-tokens' in request.headers:
                token = request.headers['x-access-tokens']

            if not token:
                return jsonify({'message': 'a valid token is missing'})

            try:
                data = dict(jwt.decode(token, app.config["SECRET_KEY"]))
                current_user = User.objects(public_id=data.get("public_id")).first()
            except Exception:
                return jsonify({'message': 'token is invalid'})

            missing_roles=[r for r in roles if r not in current_user.roles]
            if "admin" in current_user.roles:
              missing_roles=[]
            if len(missing_roles) > 0:
              return f(current_user, *args,  **kwargs)
            else:
              return jsonify({'message': 'Not permited, missing roles (%s)'%(','.join(missing_roles))})

        return decorator
    return require_token



@app.route('/register', methods=['GET', 'POST'])
def signup_user():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(public_id=str(uuid.uuid4()),
                    name=data['name'], username=data['username'], password=hashed_password, admin=False)
    new_user.save()

    return jsonify({'message': 'registered successfully'})


@app.route('/login', methods=['GET', 'POST'])
def login_user():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('could not verify', 401, {
          'WWW.Authentication': 'Basic realm: "login required"'
          })

    user = User.objects(username=auth.username).first()

    if check_password_hash(user.password_hash, auth.password):
        token = jwt.encode({'public_id': user.public_id, 'exp': datetime.datetime.utcnow(
        ) + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
        return jsonify({'token': token.decode('UTF-8')})

    return make_response('could not verify', 401, {
      'WWW.Authentication': 'Basic realm: "login required"'
      })


@app.route('/user', methods=['GET'])
def get_all_users():
    users = User.objects()

    result = []

    for user in users:
        user_data = {}
        user_data['public_id'] = user.public_id
        user_data['name'] = user.name
        user_data['password'] = user.password
        user_data['admin'] = user.admin

        result.append(user_data)

    return jsonify({'users': result})


@app.route('/authors', methods=['GET', 'POST'])
@authenticate()
def get_authors(current_user):
    authors = Author.objects()

    output = []

    for author in authors:
        author_data = {}
        author_data['name'] = author.name
        author_data['book'] = author.book
        author_data['country'] = author.country
        author_data['booker_prize'] = author.booker_prize
        output.append(author_data)

    return jsonify({'list_of_authors': output})


@app.route('/authors', methods=['POST', 'GET'])
@authenticate()
def create_author(current_user):
    data = request.get_json()

    new_authors = Author(
        name=data['name'], country=data['country'], user_id=current_user.id)
    new_authors.save()

    return jsonify({'message': 'new author created'})


@app.route('/authors/<name>', methods=['DELETE'])
@authenticate()
def delete_author(current_user, name):
    author = Author.objects(name=name, user_id=current_user.id).first()
    # author = Author.query.filter_by(name=name, user_id=current_user.id).first()
    if not author:
        return jsonify({'message': 'author does not exist'})

    author.save()

    return jsonify({'message': 'Author deleted'})

@app.route('/hostadd', methods=['PUT'])
@authenticate(['AddHost'])
def host_add(current_user):
    data = request.get_json()
    if "name" not in data:
        return jsonify({'message': ''''"name" required argument'''})
    Host(name=data.get('name'),vars=data.get('vars', {}), groups=data.get("groups",[])).save()
    return jsonify({'message': 'Host Added'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)


@app.route('/groupadd', methods=['PUT'])
@authenticate(['AddGroup'])
def group_add(current_user):
    warning=[]
    data = request.get_json()
    if "name" not in data:
        return jsonify({'message': ''''"name" required argument'''})
    

    parentgroups=data.get("parentgroups",None)
    o_parentgroup=Group.objects(name__in=parentgroups)
    for nf in Group.objects(name__nin=parentgroups):
      warning.append("Could not find parent group %s"%nf)

    childgroups=data.get("parentgroups",None)
    o_childgroups=Group.objects(name__in=childgroups)
    for nf in Group.objects(name__nin=childgroups):
      warning.append("Could not find child group %s"%nf)
    
    Group(name=data.get('name'),vars=data.get('vars', {}), childgroups=o_childgroups, parentgroups=o_parentgroup).save()
    return jsonify({'message': 'Group Added'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)