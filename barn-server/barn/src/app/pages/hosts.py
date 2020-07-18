from flask import request, jsonify, Blueprint
from app.models import User, Host, Group, Node, Role
from app.utils import list_parser, merge_args_data
from app.auth import authenticate

hosts_blueprint = Blueprint('auth', __name__, url_prefix='/auth')

@hosts_blueprint.route('/hosts', methods=['GET'])
@authenticate('getHost')
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