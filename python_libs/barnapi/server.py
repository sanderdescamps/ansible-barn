
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import jwt
import datetime
from functools import wraps
from flask import request, jsonify, make_response
from app import app
from app.models import User, Role, Host, Group, Node
from app.debug import db_init, db_flush


def authenticate(*roles):
    def require_token(f):
        @wraps(f)
        def decorator(*args, **kwargs):

            token = None

            if 'x-access-tokens' in request.headers:
                token = request.headers['x-access-tokens']
            print(token)
            if not token or token == "":
                return jsonify({'message': 'a valid token is missing'})

            try:
                data = dict(jwt.decode(token, app.config["SECRET_KEY"]))
                current_user = User.objects(
                    public_id=data.get("public_id")).first()
            except jwt.exceptions.InvalidSignatureError:
                return jsonify({'message': 'token is invalid'})
            except jwt.exceptions.ExpiredSignatureError:
                return jsonify({'message': 'token expired'})

            if current_user is None:
                return jsonify({'message': 'No valid token'})

            missing_roles = None
            if (roles is None) or (len(roles) == 0) or ("Admin" in current_user.roles):
                missing_roles = []
            else:
                missing_roles = [
                    r for r in roles if r not in current_user.roles]
            print(len(missing_roles))
            if len(missing_roles) < 1:
                return f(current_user, *args,  **kwargs)
            else:
                return jsonify({'message': 'Not permited, missing roles (%s)' % (','.join(missing_roles))})

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

        result.append(user_data)

    return jsonify({'users': result})


@app.route('/hostadd', methods=['PUT'])
@authenticate('AddHost')
def host_add(current_user):
    data = request.get_json()
    if "name" not in data:
        return jsonify({'message': ''''"name" required argument'''})
    Host(name=data.get('name'), vars=data.get(
        'vars', {}), groups=data.get("groups", [])).save()
    return jsonify({'message': 'Host Added'})


@app.route('/groupadd', methods=['PUT'])
@authenticate('AddGroup')
def group_add(current_user):
    warning = []
    data = request.get_json()
    if "name" not in data:
        return jsonify({'message': ''''"name" required argument'''})

    group = Group(name=data.get('name'), vars=data.get('vars', {}))
    group.save()
    parentgroups = data.get("parent_groups", None)
    if parentgroups is not None:
        o_parentgroup = Group.objects(name__in=parentgroups)
        if o_parentgroup is not None:
            group.parent_groups.extend(o_parentgroup)
            for g in o_parentgroup:
                g.child_groups.append(group)
                g.save()
        for not_found in Group.objects(name__nin=parentgroups):
            warning.append("Could not find parent group %s" % (not_found))

    childgroups = data.get("child_groups", None)
    if childgroups is not None:
        o_childgroups = Group.objects(name__in=childgroups)
        if o_childgroups is not None:
            group.child_groups.extend(o_childgroups)
            for g in o_childgroups:
                g.parent_groups.append(group)
                g.save()
        for not_found in Group.objects(name__nin=childgroups):
            warning.append("Could not find child group %s" % (not_found))

    group.save()
    return jsonify({'message': 'Group Added'})


@app.route('/init', methods=['PUT'])
@authenticate()
def init(current_user):
    db_init()
    return jsonify({'message': 'Database has been reseted'})


@app.route('/flush', methods=['DELETE'])
@authenticate("admin")
def flush(current_user):
    db_flush()
    return jsonify({'message': 'Database has been cleared'})


@app.route('/query', methods=['GET', 'POST'])
@authenticate("ReadOnly")
def query(current_user):
    data = request.get_json()
    if "name" not in data:
        return jsonify({'message': ''''"name" required argument'''})
    if isinstance(data.get("name"), str):
        data["name"] = [data.get("name")]
    o_node = Node.objects(name__in=data.get("name"))

    if data.get("hide_id", True):
        o_node = o_node.exclude("id")

    if o_node is not None:
        return jsonify(o_node)
    else:
        return jsonify({'var': 'Host not found'})

@app.route('/setvar', methods=['PUT'])
@authenticate("ReadOnly")
def set_var(current_user):
    data = request.get_json()
    if "name" not in data:
        return jsonify({'message': ''''"name" required argument'''})
    o_host = Host.objects(name=data.get("name")).first()
    if o_host is not None:
        o_host.vars.update(data.get("vars",{}))
        o_host.save()
    else:
        return jsonify({'message': 'host not found'})
    return jsonify({'message': 'add variables to object', "host": o_host })



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

