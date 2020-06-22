from flask import Flask, request, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import jwt
import datetime
from functools import wraps

from flask_mongoengine import MongoEngine
from mongoengine import StringField, IntField, BooleanField


app = Flask(__name__)

app.config['SECRET_KEY'] = "mlqdifjqmlsdfkjqmldkfjmoifjqmlsdjnm"
app.config['MONGODB_SETTINGS'] = dict(
    db="inventory",
    host="192.168.56.3",
    username="admin-user",
    password="jfldmdpdeiehjkHGSthjjhDdfghhFdf",
    authentication_source="admin"
)

db = MongoEngine(app)


class User(db.Document):
    public_id = StringField(required=True)
    name = StringField()
    username = StringField(required=True, unique=True)
    password = StringField()
    admin = BooleanField(default=False)

    def __repr__(self):
        return '<User %r>' % (self.name)


class Author(db.Document):
    name = IntField(required=True, unique=True)
    country = StringField(required=True)
    user_id = IntField(required=True)

    def __repr__(self):
        return '<Author %r>' % (self.name)


def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):

        token = None

        if 'x-access-tokens' in request.headers:
            token = request.headers['x-access-tokens']

        if not token:
            return jsonify({'message': 'a valid token is missing'})

        try:
            data = jwt.decode(token, app.config["SECRET_KEY"])
            current_user = User.objects(public_id=data['public_id'])[0]
            # current_user = Users.query.filter_by(public_id=data['public_id']).first()
        except Exception:
            return jsonify({'message': 'token is invalid'})

        return f(current_user, *args,  **kwargs)
    return decorator


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

    # user = Users.query.filter_by(name=auth.username).first()
    user = User.objects(username=auth.username)[0]

    if check_password_hash(user.password, auth.password):
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
@token_required
def get_authors(current_user, public_id):
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
@token_required
def create_author(current_user):
    data = request.get_json()

    new_authors = Author(
        name=data['name'], country=data['country'], user_id=current_user.id)
    new_authors.save()

    return jsonify({'message': 'new author created'})


@app.route('/authors/<name>', methods=['DELETE'])
@token_required
def delete_author(current_user, name):
    author = Author.objects(name=name, user_id=current_user.id)[0]
    # author = Author.query.filter_by(name=name, user_id=current_user.id).first()
    if not author:
        return jsonify({'message': 'author does not exist'})

    author.save()

    return jsonify({'message': 'Author deleted'})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
