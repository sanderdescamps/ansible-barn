from flask import request, Blueprint
from mongoengine.errors import NotUniqueError
from http import HTTPStatus
from app.models import Host, Group
from app.utils import merge_args_data, list_parser
from app.utils.formater import ResponseFormater
from app.auth import authenticate



host_pages = Blueprint('host', __name__)


@host_pages.route('/hosts', methods=['GET'])
@authenticate('getHost')
def get_hosts(current_user=None):
    resp = ResponseFormater()
    args = merge_args_data(request.args, request.get_json(silent=True))

    query_args = dict()
    if "name" in args:
        query_args["name"] = args.get("name")
    resp.add_result(Host.objects(**query_args))
    return resp.get_response()

@host_pages.route('/hosts', methods=['PUT'])
@authenticate('addHost')
def put_hosts(current_user=None):
    resp = ResponseFormater()
    args = merge_args_data(request.args, request.get_json(silent=True))
    

    name = args.get("name", None)
    if name is None:
        resp.failed(msg='name not defined')
        return resp.get_response()

    # Create Host
    o_host = Host.objects(name=name).first()
    if o_host is None:
        try:
            o_host = Host(name=name)
            resp.succeed(changed=True, status=HTTPStatus.CREATED)
        except NotUniqueError:
            resp.failed(msg='Duplicate Node: %s already exist' % (args.get("name")))
            return resp.get_response()

    
    # Set variables
    barn_vars = args.get("vars", {})
    for k, v in barn_vars.items():
        if o_host.vars.get(k, None) != v:
            o_host.vars[k] = v
            resp.changed()

    # Delete variables
    vars_to_remove = args.get("vars_absent", [])
    for var_to_remove in vars_to_remove:
        if var_to_remove in o_host.vars:
            del o_host.vars[var_to_remove]
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
                print("create %s"%(group))
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
            g.save()
            resp.changed()
    for g in list(set(o_groups_add_list)):
        if o_host not in g.hosts:
            g.hosts.append(o_host)
            g.save()
            resp.changed()

    return resp.get_response()


@host_pages.route('/hosts', methods=['DELETE'])
@authenticate('deleteHost')
def delete_hosts(current_user=None):
    resp = ResponseFormater()
    query_args = dict()
    if "name" in request.args:
        query_args["name__in"] = list_parser(request.args.get("name"))
    else:
        resp.failed(msg='name not defined')
        return resp.get_response()

    o_hosts = Host.objects(**query_args)
    if o_hosts.count() < 1:
        resp.failed(msg='%s not found' % (request.args.get('name')))
        return resp.get_response()
    s_hosts = ','.join(o_hosts.scalar('name'))
    o_hosts.delete()
    resp.succeed(msg='%s have been deleted' % (s_hosts))
    return resp.get_response()
