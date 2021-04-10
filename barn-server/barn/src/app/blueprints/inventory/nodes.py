import re
from flask import request
from flask_smorest import Blueprint
from flask_login import login_required
from app.models import Node
from app.utils import merge_args_data, list_parser, boolean_parser
from app.blueprints.inventory.hosts import put_hosts
from app.blueprints.inventory.groups import put_groups
from app.utils.formater import ResponseBuilder
from app.utils.schemas import NodeQueryArgsSchema, NodeSchema

node_pages = Blueprint('nodes', __name__)


@node_pages.route('/api/v1/inventory/nodes', methods=['GET'])
@node_pages.arguments(NodeQueryArgsSchema, location='query', as_kwargs=True)
@login_required
def get_nodes(**kwargs):
    return _get_nodes(**kwargs)

@node_pages.route('/api/v1/inventory/nodes', methods=['POST'])
@node_pages.arguments(NodeQueryArgsSchema, location='query', as_kwargs=True)
@node_pages.arguments(NodeQueryArgsSchema, location='json', as_kwargs=True)
@login_required
def post_nodes(**kwargs):
    return _get_nodes(**kwargs)

def _get_nodes(**kwargs):
    resp = ResponseBuilder()
    query_args = dict()
    if "name" in kwargs:     
        if boolean_parser(kwargs.get("regex",False)):
            regex_name = re.compile("^{}$".format(kwargs.get("name").strip(" ").lstrip("^").rstrip("$")))
            query_args["name"] = regex_name
        else:
            regex_name = re.compile(r"^{}$".format(re.escape(kwargs.get("name")).replace("\*",".*")))
            query_args["name"] = regex_name
    if "type" in kwargs:
        node_type = kwargs.get("type")
        if node_type.lower() == "host":
            query_args["_cls"] = "Node.Host"
        elif node_type.lower() == "group":
            query_args["_cls"] = "Node.Group"
    o_nodes = Node.objects(**query_args)
    resp.add_result(o_nodes)
    return resp.get_response()

# @node_pages.route('/api/v1/inventory/nodes', methods=['PUT'])
# @login_required
# def put_nodes():
#     resp = ResponseBuilder()
#     args = merge_args_data(request.args, request.get_json(silent=True))
#     node_type = args.get("type", None)
#     if not node_type:
#         resp.failed(msg='type not defined')
#         return resp.get_response()
#     elif node_type.lower() == "host":
#         return put_hosts(resp=resp)
#     elif node_type.lower() == "group":
#         return put_groups(resp=resp)
#     else:
#         resp.failed(msg='unknown type: %s' % (node_type))
#         return resp.get_response()


# @node_pages.route('/api/v1/inventory/nodes', methods=['DELETE'])
# @login_required
# def delete_nodes(**kwargs):
#     resp = ResponseBuilder()
#     query_args = dict()
#     if "name" in kwargs:
#         query_args["name__in"] = list_parser(kwargs.get("name"))
#     else:
#         resp.failed(msg='name not defined')
#         return resp.get_response()


#     o_nodes = Node.objects(**query_args)
#     if o_nodes.count() < 1:
#         resp.failed(msg='%s not found' % (kwargs.get('name')))
#         return resp.get_response()
#     s_nodes = ','.join(o_nodes.scalar('name'))
#     o_nodes.delete()
#     resp.succeed(msg='%s have been deleted' % (s_nodes))
#     return resp.get_response()