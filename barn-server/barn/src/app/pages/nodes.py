from flask import request, jsonify, Blueprint
from app.models import Node
from app.utils import merge_args_data
from app.auth import authenticate
from app.pages.hosts import put_hosts
from app.pages.groups import put_groups

node_pages = Blueprint('nodes', __name__)


@node_pages.route('/nodes', methods=['GET'])
@authenticate('getNode')
def get_nodes(current_user=None):
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


@node_pages.route('/nodes', methods=['PUT'])
@authenticate('addNode')
def post_nodes(current_user=None):
    args = merge_args_data(request.args, request.get_json(silent=True))
    node_type = args.get("type", None)
    if not node_type:
        return jsonify(error='type not defined'), 400
    elif node_type.lower() == "host":
        return put_hosts(current_user=current_user)
    elif node_type.lower() == "group":
        return put_groups(current_user=current_user)
    else:
        return jsonify(error='unknown type: %s' % (node_type)), 400


@node_pages.route('/nodes', methods=['DELETE'])
@authenticate('deleteNode')
def delete_nodes(current_user=None):
    query_args = dict()
    if "name" in request.args:
        query_args["name__in"] = request.args.get("name").split(',')
    else:
        return jsonify(error='name not defined'), 400

    o_nodes = Node.objects(**query_args)
    if o_nodes.count() < 1:
        return jsonify(error='%s not found' % (request.args.get('name'))), 400
    s_nodes = ','.join(o_nodes.scalar('name'))
    o_nodes.delete()
    return jsonify({'message': '%s have been deleted' % (s_nodes)})
