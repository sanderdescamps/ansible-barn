
import uuid
import datetime
from functools import wraps
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request, jsonify, make_response, redirect, url_for
from app import app
from app.models import User, Host, Group, Node
from app.debug import db_init, db_flush
from mongoengine.errors import NotUniqueError



def authenticate(*roles):
    def require_token(f):
        @wraps(f)
        def decorator(*args, **kwargs):
            current_user=None
            
            token = request.headers.get('x-access-tokens', None) 
            if token is not None and token != "":
                try:
                    data = dict(jwt.decode(token, app.config["SECRET_KEY"]))
                    current_user = User.objects(public_id=data.get("public_id")).first()
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

            if not current_user.roles_check(roles):
                return jsonify(error='Not permited, missing roles (%s)' % (','.join(current_user.missing_roles(roles)))), 401

            return f(*args, current_user=current_user, **kwargs)

        return decorator
    return require_token


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
    print(user.password_hash)
    if check_password_hash(user.password_hash, auth.password):
        token = jwt.encode({'public_id': user.public_id, 'exp': datetime.datetime.utcnow(
        ) + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
        print("token: %s"%token.decode('UTF-8'))
        return jsonify({'token': token.decode('UTF-8')})

    return make_response('could not verify', 401, {
        'WWW.Authentication': 'Basic realm: "login required"'
    })


@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.objects()
    return jsonify({"result":users.exclude("id")})

@app.route('/nodes', methods=['GET'])
@authenticate('getNode')
def get_nodes(current_user=None):
    args = request.args.copy()
    data = request.get_json(silent=True)
    if data:
        for k,v in data.items():
            args[k] = v

    query_args=dict()
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
    query_args=dict()
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
            return make_response('unknown type: %s'%(t), 400)
    except NotUniqueError as e:
        return make_response('Duplicate Node: %s already exist'%(request.args.get("name")), 400)

    return jsonify({'message': 'Host Added'})


@app.route('/hosts', methods=['PUT'])
@authenticate('addHost')
def put_host(current_user=None):
    changed = False
    args = request.args.copy()
    data = request.get_json()
    for k,v in data.items():
        args[k] = v
    query_args=dict()
    
    name = args.get("name",None)
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
            return jsonify(error='Duplicate Node: %s already exist'%(args.get("name"))), 400

    # Set variables
    barn_vars = data.get("vars", {})
    for k,v in barn_vars.items():
        if o_node.vars.get(k,None) != v:
            o_node.vars[k] = v
            changed = True
    
    if changed:
        o_node.save()

    return jsonify({'host': o_node, 'changed': changed})


@app.route('/nodes', methods=['DELETE'])
@authenticate('deleteNode')
def delete_nodes(current_user=None):
    query_args=dict()
    if "name" in request.args: 
        query_args["name__in"] = request.args.get("name").split(',')
    else:
        return make_response('name not defined', 400)
    
    o_nodes = Node.objects(**query_args)
    if o_nodes.count() < 1:
        return make_response('%s not found'%(request.args.get('name')), 400)
    s_nodes = ','.join(o_nodes.scalar('name'))
    o_nodes.delete()
    return jsonify({'message': '%s have been deleted'%(s_nodes)})


@app.route('/test', methods=['GET'])
@authenticate()
def test(current_user=None):
    return make_response("'name' required parameter", 400) 


# @app.route('/host/add', methods=['PUT'])
# @authenticate('AddHost')
# def host_add(current_user=None):
#     data = request.get_json()
#     if "name" not in data:
#         return jsonify({'message': ''''"name" required argument'''})
#     Host(name=data.get('name'), vars=data.get(
#         'vars', {}), groups=data.get("groups", [])).save()
#     return jsonify({'message': 'Host Added'})

# @app.route('/host/delete', methods=['DELETE'])
# @authenticate('DeleteHost')
# def host_delete(current_user=None):
#     data = request.get_json()
#     if "name" not in data:
#         return jsonify({'message': ''''"name" required argument'''})
    
#     if isinstance(data.get("name"), str):
#         data["name"] = [data.get("name")]
#     o_node = Node.objects(name__in=data.get("name")).delete()

#     return jsonify({'message': 'Host deleted'})

# @app.route('/groupadd', methods=['PUT'])
# @authenticate('AddGroup')
# def group_add(current_user=None):
#     warning = []
#     data = request.get_json()
#     if "name" not in data:
#         return jsonify({'message': ''''"name" required argument'''})

#     group = Group(name=data.get('name'), vars=data.get('vars', {}))
#     group.save()
#     parentgroups = data.get("parent_groups", None)
#     if parentgroups is not None:
#         o_parentgroup = Group.objects(name__in=parentgroups)
#         if o_parentgroup is not None:
#             group.parent_groups.extend(o_parentgroup)
#             for g in o_parentgroup:
#                 g.child_groups.append(group)
#                 g.save()
#         for not_found in Group.objects(name__nin=parentgroups):
#             warning.append("Could not find parent group %s" % (not_found))

#     childgroups = data.get("child_groups", None)
#     if childgroups is not None:
#         o_childgroups = Group.objects(name__in=childgroups)
#         if o_childgroups is not None:
#             group.child_groups.extend(o_childgroups)
#             for g in o_childgroups:
#                 g.parent_groups.append(group)
#                 g.save()
#         for not_found in Group.objects(name__nin=childgroups):
#             warning.append("Could not find child group %s" % (not_found))

#     group.save()
#     return jsonify({'message': 'Group Added'})


@app.route('/init', methods=['PUT'])
@authenticate()
def init(current_user=None):
    db_init()
    return jsonify({'message': 'Database has been reseted'})


@app.route('/flush', methods=['DELETE'])
@authenticate("admin")
def flush(current_user=None):
    db_flush()
    return jsonify({'message': 'Database has been cleared'})


# @app.route('/query', methods=['GET', 'POST'])
# @authenticate("ReadOnly")
# def query(current_user=None):
#     data = request.get_json()
#     if "name" not in data:
#         return jsonify({'message': ''''"name" required argument'''})

#     nodes = data.get("name")   
#     if isinstance(data.get("name"), str):
#         nodes = [nodes]
#     o_nodes = Node.objects(name__in=nodes)

#     result = {}
#     for n in nodes:
#         o_node = Node.objects(name=n).first()
#         if o_node: 
#             d_node = o_node.to_dict()
#             d_node["failed"] = False
#             result[n]=d_node
#         else:
#             result[n]={
#                 "msg": "Node not found",
#                 "failed": True
#             }
#     return jsonify(result)

# @app.route('/setvar', methods=['PUT'])
# @authenticate("ReadOnly")
# def set_var(current_user=None):
#     data = request.get_json()
#     if "name" not in data:
#         return jsonify({'message': ''''"name" required argument'''})
#     o_node = Node.objects(name=data.get("name")).first()
#     if o_node is not None:
#         o_node.vars.update(data.get("vars",{}))
#         o_node.save()
#     else:
#         return jsonify({'message': 'host not found'})
#     return jsonify({'message': 'add variables to object', "result": o_node })



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

