
import uuid
import datetime
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, jsonify, make_response, redirect, url_for
from mongoengine.errors import NotUniqueError
from app import app
from app.models import User, Host, Group, Node
from app.debug import db_init, db_flush
from app.auth import authenticate


@app.route('/register', methods=['GET', 'POST'])
def signup_user():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = User(public_id=str(uuid.uuid4()),
                    name=data['name'], username=data['username'],
                    password_hash=hashed_password, admin=False)
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
    if user is None:
        return make_response('Could not login', 401, {
            'WWW.Authentication': 'Basic realm: "login required"'
        })
    if check_password_hash(user.password_hash, auth.password):
        token = jwt.encode({'public_id': user.public_id, 'exp': datetime.datetime.utcnow(
        ) + datetime.timedelta(minutes=30)}, app.config['TOKEN_ENCRYPTION_KEY'])
        print("token: %s" % token.decode('UTF-8'))
        return jsonify({'token': token.decode('UTF-8')})

    return make_response('could not verify', 401, {
        'WWW.Authentication': 'Basic realm: "login required"'
    })


@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.objects()
    return jsonify({"result": users.exclude("id")})


@app.route('/nodes', methods=['GET'])
@authenticate('getNode')
def get_nodes(current_user=None):
    args = request.args.copy()
    data = request.get_json(silent=True)
    if data:
        for k, v in data.items():
            args[k] = v

    query_args = dict()
    if "name" in args:
        query_args["name"] = args.get("name")
    if "type" in args:
        t = args.get("type")
        if t.lower() == "host":
            query_args["_cls"] = "Node.Host"
        elif t.lower() == "group":
            query_args["_cls"] = "Node.Group"
    o_nodes = Node.objects(**query_args)
    return jsonify({'results': o_nodes})


@app.route('/hosts', methods=['GET'])
@authenticate()
def get_hosts(current_user=None):
    return redirect(url_for('get_nodes', type="host", **request.args))


@app.route('/groups', methods=['GET'])
@authenticate('getGroup')
def get_groups(current_user=None):
    return redirect(url_for('get_nodes', type="group", **request.args))


@app.route('/nodes', methods=['POST'])
@authenticate('addNode')
def post_nodes(current_user=None):
    query_args = dict()
    if "name" in request.args:
        query_args["name"] = request.args.get("name")
    else:
        return make_response('name not defined', 400)

    if "type" not in request.args:
        return make_response('type not defined', 400)

    try:
        t = request.args.get("type")
        if t.lower() == "host":
            if "groups" in request.args:
                groups = request.args.get("groups").split(',')
                o_groups = Group.objects(name__in=groups)
                query_args["groups"] = o_groups
            Host(**query_args).save()
        elif t.lower() == "group":
            if "parent_groups" in request.args:
                parent_groups = request.args.get("parent_groups").split(',')
                o_parent_groups = Group.objects(name__in=parent_groups)
                query_args["parent_groups"] = o_parent_groups
            if "child_groups" in request.args:
                child_groups = request.args.get("child_groups").split(',')
                o_child_groups = Group.objects(name__in=child_groups)
                query_args["child_groups"] = o_child_groups
            Group(**query_args).save()
        else:
            return make_response('unknown type: %s' % (t), 400)
    except NotUniqueError as e:
        return make_response('Duplicate Node: %s already exist' % (request.args.get("name")), 400)

    return jsonify({'message': 'Host Added'})


@app.route('/hosts', methods=['PUT'])
@authenticate('addHost')
def put_host(current_user=None):
    changed = False
    args = request.args.copy()
    data = request.get_json()
    for k, v in data.items():
        args[k] = v
    query_args = dict()

    name = args.get("name", None)
    if name is None:
        return jsonify(error='name not defined'), 400

    # Create Host
    o_node = Host.objects(name=name).first()
    if o_node is None:
        try:
            if "groups" in args:
                groups = args.get("groups").split(',')
                o_groups = Group.objects(name__in=groups)
                query_args["groups"] = o_groups
            o_node = Host(**query_args)
            changed = True
        except NotUniqueError:
            return jsonify(error='Duplicate Node: %s already exist' % (args.get("name"))), 400

    # Set variables
    barn_vars = data.get("vars", {})
    for k, v in barn_vars.items():
        if o_node.vars.get(k, None) != v:
            o_node.vars[k] = v
            changed = True

    if changed:
        o_node.save()

    return jsonify({'host': o_node, 'changed': changed})


@app.route('/nodes', methods=['DELETE'])
@authenticate('deleteNode')
def delete_nodes(current_user=None):
    query_args = dict()
    if "name" in request.args:
        query_args["name__in"] = request.args.get("name").split(',')
    else:
        return make_response('name not defined', 400)

    o_nodes = Node.objects(**query_args)
    if o_nodes.count() < 1:
        return make_response('%s not found' % (request.args.get('name')), 400)
    s_nodes = ','.join(o_nodes.scalar('name'))
    o_nodes.delete()
    return jsonify({'message': '%s have been deleted' % (s_nodes)})


@app.route('/init', methods=['PUT'])
@authenticate()
def init(current_user=None):
    db_init()
    return jsonify({'message': 'Database has been reseted'})

@app.route('/flush', methods=['DELETE'])
@authenticate("admin")
def flush(current_user=None):
    db_flush()
    return jsonify({'message': 'Database has been flushed'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
