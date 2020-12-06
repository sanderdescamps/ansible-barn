from flask import request, Blueprint
from flask_login import login_required
from app.models import Node
from app.utils import merge_args_data, list_parser
from app.pages.inventory.hosts import put_hosts
from app.pages.inventory.groups import put_groups
from app.utils.formater import ResponseFormater

node_pages = Blueprint('nodes', __name__)


@node_pages.route('/api/v1/inventory/nodes', methods=['GET'])
@login_required
def get_nodes():
    resp = ResponseFormater()
    args = request.args
 
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
    resp.add_result(o_nodes)
    return resp.get_response()

@node_pages.route('/api/v1/inventory/nodes', methods=['POST'])
@login_required
def post_nodes():
    resp = ResponseFormater()
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
    resp.add_result(o_nodes)
    return resp.get_response()

@node_pages.route('/api/v1/inventory/nodes', methods=['PUT'])
@login_required
def put_nodes():
    resp = ResponseFormater()
    args = merge_args_data(request.args, request.get_json(silent=True))
    node_type = args.get("type", None)
    if not node_type:
        resp.failed(msg='type not defined')
        return resp.get_response()
    elif node_type.lower() == "host":
        return put_hosts(resp=resp)
    elif node_type.lower() == "group":
        return put_groups(resp=resp)
    else:
        resp.failed(msg='unknown type: %s' % (node_type))
        return resp.get_response()


@node_pages.route('/api/v1/inventory/nodes', methods=['DELETE'])
@login_required
def delete_nodes():
    resp = ResponseFormater()
    query_args = dict()
    if "name" in request.args:
        query_args["name__in"] = list_parser(request.args.get("name"))
    else:
        resp.failed(msg='name not defined')
        return resp.get_response()


    o_nodes = Node.objects(**query_args)
    if o_nodes.count() < 1:
        resp.failed(msg='%s not found' % (request.args.get('name')))
        return resp.get_response()
    s_nodes = ','.join(o_nodes.scalar('name'))
    o_nodes.delete()
    resp.succeed(msg='%s have been deleted' % (s_nodes))
    return resp.get_response()