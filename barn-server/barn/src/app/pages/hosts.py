from flask import request, jsonify, Blueprint
from mongoengine.errors import NotUniqueError
from app.models import Host, Group, Node
from app.utils import merge_args_data
from app.auth import authenticate


host_pages = Blueprint('host', __name__)


@host_pages.route('/hosts', methods=['GET'])
@authenticate('getHost')
def get_hosts(current_user=None):
    args = merge_args_data(request.args, request.get_json(silent=True))

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

@host_pages.route('/hosts', methods=['PUT'])
@authenticate('addHost')
def put_hosts(current_user=None):
    changed = False
    args = merge_args_data(request.args, request.get_json(silent=True))
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


@host_pages.route('/hosts', methods=['DELETE'])
@authenticate('deleteHost')
def delete_hosts(current_user=None):
    query_args = dict()
    if "name" in request.args:
        query_args["name__in"] = request.args.get("name").split(',')
    else:
        return jsonify(error='name not defined'), 400

    o_hosts = Host.objects(**query_args)
    if o_hosts.count() < 1:
        return jsonify(error='%s not found' % (request.args.get('name'))), 400
    s_hosts = ','.join(o_hosts.scalar('name'))
    o_hosts.delete()
    return jsonify({'message': '%s have been deleted' % (s_hosts)})
