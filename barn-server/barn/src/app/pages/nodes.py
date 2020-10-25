from flask import request, Blueprint
from app.models import Node
from app.utils import merge_args_data, list_parser
from app.auth import authenticate
from app.pages.hosts import put_hosts
from app.pages.groups import put_groups
from app.utils.formater import ResponseFormater

node_pages = Blueprint('nodes', __name__)


@node_pages.route('/nodes', methods=['GET'])
@authenticate('getNode')
def get_nodes(current_user=None):
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


@node_pages.route('/nodes', methods=['PUT'])
@authenticate('addNode')
def post_nodes(current_user=None):
    resp = ResponseFormater()
    args = merge_args_data(request.args, request.get_json(silent=True))
    node_type = args.get("type", None)
    if not node_type:
        resp.failed(msg='type not defined')
        return resp.get_response()
    elif node_type.lower() == "host":
        return resp + put_hosts(current_user=current_user)
    elif node_type.lower() == "group":
        return resp + put_groups(current_user=current_user)
    else:
        resp.failed(msg='unknown type: %s' % (node_type))
        return resp.get_response()


@node_pages.route('/nodes', methods=['DELETE'])
@authenticate('deleteNode')
def delete_nodes(current_user=None):
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