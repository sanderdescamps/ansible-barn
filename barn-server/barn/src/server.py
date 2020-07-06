
import uuid
import datetime
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, jsonify, make_response, redirect, url_for
from mongoengine.errors import NotUniqueError
from app import app
from app.models import User, Host, Group, Node, Role
from app.auth import authenticate
from app.utils import list_parser

def _merge_args_data(args, data=None):
    output = args.copy()
    if data:
        for k, v in data.items():
            output[k] = v
    return output


@app.route('/register', methods=['GET', 'POST'])
def signup_user():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    try:
        new_user = User(public_id=str(uuid.uuid4()),
                        name=data['name'], username=data['username'],
                        password_hash=hashed_password, admin=False)
        new_user.save()
    except NotUniqueError:
        return jsonify(error='user already exists'), 400

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
    args = _merge_args_data(request.args, request.get_json(silent=True))

    query_args = dict()
    if "name" in args:
        query_args["name"] = args.get("name")
    if "type" in args:
        node_type = args.get("type")
        if node_type.lower() == "host":
            query_args["_cls"] = "Node.Host"
        elif node_type.lower() == "group":
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
@authenticate('addHost')
def post_hosts(current_user=None):
    args = _merge_args_data(request.args, request.get_json(silent=True))
    query_args = dict()
    if "name" in args:
        query_args["name"] = args.get("name")
    else:
        return make_response('name not defined', 400)

    try:
        o_groups = []
        if "groups" in args:
            groups = list_parser(args.get("groups"))
            o_groups = Group.objects(name__in=groups)
            query_args["groups"] = o_groups
        o_host = Host(**query_args)
        o_host.save()
        for o_group in o_groups:
            o_group.update(add_to_set__hosts=o_host)

    except NotUniqueError:
        return make_response('Duplicate Host: %s already exist' % (args.get("name")), 400)

    return jsonify({'message': 'Host Added'})


@app.route('/groups', methods=['POST'])
@authenticate('getGroup')
def post_groups(current_user=None):
    args = _merge_args_data(request.args, request.get_json(silent=True))

    query_args = dict()
    if "name" in args:
        query_args["name"] = args.get("name")
    else:
        return make_response('name not defined', 400)

    try:
        if "child_groups" in args:
            child_groups = list_parser(args.get("child_groups"))
            o_child_groups = Group.objects(name__in=child_groups)
            query_args["child_groups"] = o_child_groups
        o_group = Group(**query_args)
        o_group.save()

        if "parent_groups" in args:
            parent_groups = list_parser(args.get("parent_groups"))
            o_parent_groups = Group.objects(name__in=parent_groups)
            for o_parent_group in o_parent_groups:
                o_parent_group.update(add_to_set__child_groups=o_group)
    except NotUniqueError:
        return make_response('Duplicate Group: %s already exist' % (args.get("name")), 400)

    return jsonify({'message': 'Group Added'})


@app.route('/nodes', methods=['POST'])
@authenticate('addNode')
def post_nodes(current_user=None):
    args = _merge_args_data(request.args, request.get_json(silent=True))
    node_type = args.get("type", None)
    if not node_type:
        return make_response('type not defined', 400)
    elif node_type.lower() == "host":
        return post_hosts(current_user=current_user)
    elif node_type.lower() == "group":
        return post_groups(current_user=current_user)
    else:
        return make_response('unknown type: %s' % (node_type), 400)


@app.route('/hosts', methods=['PUT'])
@authenticate('addHost')
def put_host(current_user=None):
    changed = False
    args = _merge_args_data(request.args, request.get_json(silent=True))
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
    barn_vars = args.get("vars", {})
    for k, v in barn_vars.items():
        if o_node.vars.get(k, None) != v:
            o_node.vars[k] = v
            changed = True

    # Delete variables
    vars_to_remove = args.get("remove_vars", [])
    for var_to_remove in vars_to_remove:
        if var_to_remove in o_node.vars:
            del o_node.vars[var_to_remove]
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
    Role.objects().delete()
    r_admin = Role(name="Admin", description="Allow anything")
    r_admin.save()
    Role(name="AddHost", description="Add a host to the inventory").save()
    Role(name="AddGroup", description="Add a group to the inventory").save()
    Role(name="ReadOnly", description="Read access on inventory").save()
    Role(name="Query", description="Read access on inventory").save()

    User.objects().delete()
    user_1 = User(name="Sander Descamps", username="sdescamps",
            password="testpassword")
    user_1.roles.append(r_admin)
    user_1.save()

    Host.objects().delete()
    Host(name="srvplex01.myhomecloud.be").save()
    Host(name="srvdns01.myhomecloud.be").save()
    Host(name="srvdns02.myhomecloud.be").save()

    Group.objects().delete()
    Group(name="dns_servers").save()
    Group(name="all_servers").save()
    return jsonify({'message': 'Database has been reseted'})


@app.route('/flush', methods=['DELETE'])
@authenticate("admin")
def flush(current_user=None):
    Host.objects().delete()
    Group.objects().delete()
    return jsonify({'message': 'Database has been flushed'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
