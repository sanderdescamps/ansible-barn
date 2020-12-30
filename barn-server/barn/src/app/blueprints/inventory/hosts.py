from flask import request, Blueprint
from flask_login import login_required
from mongoengine.errors import NotUniqueError
from http import HTTPStatus
from app.models import Host, Group
from app.utils import merge_args_data, list_parser
from app.utils.formater import ResponseFormater


host_pages = Blueprint('host', __name__)


@host_pages.route('/api/v1/inventory/hosts', methods=['GET'])
@login_required
def get_hosts(resp=None):
    if resp is None:
        resp = ResponseFormater()
    args = request.args

    query_args = dict()
    if "name" in args:
        query_args["name"] = args.get("name")
    resp.add_result(Host.objects(**query_args))
    return resp.get_response()

@host_pages.route('/api/v1/inventory/hosts', methods=['POST'])
@login_required
def post_hosts():
    resp = ResponseFormater()
    args = merge_args_data(request.args, request.get_json(silent=True))

    query_args = dict()
    if "name" in args:
        query_args["name"] = args.get("name")
    resp.add_result(Host.objects(**query_args))
    return resp.get_response()


@host_pages.route('/api/v1/inventory/hosts', defaults={'action': "present"}, methods=['PUT'])
@host_pages.route('/api/v1/inventory/hosts/<action>', methods=['PUT'])
@login_required
def put_hosts(action=None, resp=None):
    if resp is None:
        resp = ResponseFormater()
    args = merge_args_data(request.args, request.get_json(silent=True))
    

    name = args.get("name", None)
    if name is None:
        resp.failed(msg='name not defined')
        return resp.get_response()

    # Create Host
    o_host = Host.objects(name=name).first()
    if o_host is not None and action == "add":
        resp.failed(msg='%s already exist' % (args.get("name")))
        return resp.get_response()
    elif o_host is None:
        if action == "update":
            resp.failed(msg='Host not found: %s Does not exist' % (args.get("name")))
            return resp.get_response()
        else:
            try:
                o_host = Host(name=name)
                resp.succeed(changed=True, msg="Create host {}".format(name), status=HTTPStatus.CREATED)
            except NotUniqueError:
                resp.failed(msg='%s already exist' % (args.get("name")))
                return resp.get_response()

    
    # Set variables
    barn_vars = args.get("vars", {})
    if action == "set" and barn_vars != o_host.vars:
        o_host.vars = {}
        resp.changed()
        resp.add_message("Reset host variables")

    for k, v in barn_vars.items():
        if o_host.vars.get(k, None) != v:
            o_host.vars[k] = v
            resp.changed()
            resp.add_message("Change variable: {}".format(k))

    # Delete variables
    if action != "add":
        vars_to_remove = args.get("vars_absent", [])
        for var_to_remove in vars_to_remove:
            if var_to_remove in o_host.vars:
                del o_host.vars[var_to_remove]
                resp.add_message("Remove variable: {}".format(var_to_remove))
                resp.changed()

    # Save Host
    if resp.get_changed():
        o_host.save()

    # Add host to group
    o_groups_remove_list = []
    o_groups_add_list = []
    if args.get("groups", False):
        groups = list_parser(args.get("groups"))
        for group in groups:
            o_group = Group.objects(name=group).first()
            if not o_group and args.get('create_groups', True):
                o_group = Group(name=group)
                resp.changed()
                resp.add_message("Create {} group".format(group))
            if o_group:
                o_groups_add_list.append(o_group)

    if args.get("groups_present", False):
        groups = list_parser(args.get("groups_present"))
        for group in groups:
            o_group = Group.objects(name=group).first()
            if not o_group and args.get('create_groups', True):
                o_group = Group(name=group)
            if o_group:
                o_groups_add_list.append(o_group)
    if args.get("groups_set", False) and not any(k in args for k in ("groups", "groups_present", "groups_absent")):
        groups = list_parser(args.get("groups_set"))

        o_groups_remove = Group.objects(name__not__in=groups, hosts__in=[o_host])
        for g in o_groups_remove:
            o_groups_remove_list.append(g)
        
        for group in groups:
            o_group = Group.objects(name=group).first()
            if not o_group and args.get('create_groups', True):
                o_group = Group(name=group)
            if o_group:
                o_groups_add_list.append(o_group)
    if args.get("groups_absent", False):
        groups = list_parser(args.get("groups_absent"))
        o_groups_remove = Group.objects(name__in=groups)
        for g in o_groups_remove:
            o_groups_remove_list.append(g)
    for g in list(set(o_groups_remove_list)):
        if o_host in g.hosts:
            g.hosts.remove(o_host)
            resp.add_message("Remove {} from {} group".format(name, g.name))
            g.save()
            resp.changed()
    for g in list(set(o_groups_add_list)):
        if o_host not in g.hosts:
            g.hosts.append(o_host)
            resp.add_message("Add {} into {} group".format(name, g.name))
            g.save()
            resp.changed()

    return resp.get_response()


@host_pages.route('/api/v1/inventory/hosts', methods=['DELETE'])
@login_required
def delete_hosts():
    resp = ResponseFormater()
    args = merge_args_data(request.args, request.get_json(silent=True))
    query_args = dict()
    if "name" in args:
        query_args["name__in"] = list_parser(args.get("name"))
    else:
        resp.failed(msg='name not defined')
        return resp.get_response()

    o_hosts = Host.objects(**query_args)
    
    

    if o_hosts.count() < 1:
        resp.failed(msg='%s not found' % (args.get('name')))
    else:
        #Remove host from all groups where the host is used
        Group.objects(hosts__in=o_hosts).update(pull_all__hosts=o_hosts) 
        s_hosts = ','.join(o_hosts.scalar('name'))
        o_hosts.delete()
        resp.succeed(msg='Delete host %s' % (s_hosts), changed=True)
    return resp.get_response()
