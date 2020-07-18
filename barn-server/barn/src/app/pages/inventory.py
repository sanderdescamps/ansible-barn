from flask import request, jsonify, Blueprint
from app.models import Node
from app.utils import merge_args_data, list_parser
from app.auth import authenticate

inventory_pages = Blueprint('inventory', __name__)

@inventory_pages.route('/inventory', methods=['GET'])
@authenticate()
def get_ansible_inventory(current_user=None):
    args = merge_args_data(request.args, request.get_json(silent=True))
    name = list_parser(args.get("name", None))
    query_args = dict()
    if name is not None:
        query_args["name__in"] = name
    else:
        return jsonify(error='name not defined'), 400

    o_nodes = Node.objects(**query_args)

    o_hosts = []
    for o_node in o_nodes:
        o_hosts.extend(o_node.get_hosts())
    o_hosts = list(set(o_hosts))
    s_hosts = []
    for o_host in o_hosts:
        s_hosts.append(o_host.name)

    return jsonify({'results': s_hosts, "o_hosts": o_hosts})