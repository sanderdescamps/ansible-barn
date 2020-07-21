from flask import Blueprint, request
from mongoengine.errors import NotUniqueError
from http import HTTPStatus
from app.utils import list_parser, merge_args_data
from app.auth import authenticate
from app.models import Group, Host
from app.utils.formater import ResponseFormater


group_pages = Blueprint('group', __name__)


@group_pages.route('/groups', methods=['GET'])
@authenticate('getGroup')
def get_groups(current_user=None):
    resp = ResponseFormater()
    args = merge_args_data(request.args, request.get_json(silent=True))

    query_args = dict()
    if "name" in args:
        query_args["name"] = args.get("name")
    o_groups = Group.objects(**query_args)
    resp.add_result(o_groups)
    return resp.get_response()


@group_pages.route('/groups', methods=['PUT'])
@authenticate('getGroup')
def put_groups(current_user=None):
    resp = ResponseFormater()
    args = merge_args_data(request.args, request.get_json(silent=True))

    name = args.get("name", None)
    if name is None:
        resp.failed(msg='name not defined')
        return resp.get_response()

    #Create Group
    o_group = Group.objects(name=name).first()
    if o_group is None:
        try:
            query_args = dict(name=name)
            o_group = Group(**query_args)
            resp.succeed(changed=True, status=HTTPStatus.CREATED)
        except NotUniqueError:
            resp.failed(msg='Duplicate Group: %s already exist' % (name))
            return resp.get_response()
    
    #Set child Groups
    if "child_groups" in args:
        child_groups = list_parser(args.get("child_groups"))
        o_child_groups = Group.objects(name__in=child_groups)
        o_group["child_groups"] = o_child_groups
        resp.changed()
    
    #Set Hosts
    if "hosts" in args:
        hosts = list_parser(args.get("hosts"))
        o_hosts = Host.objects(name__in=hosts)
        o_group["hosts"] = o_hosts
        resp.changed()
    
    #Set variables
    barn_vars = args.get("vars", {})
    for k, v in barn_vars.items():
        if o_group.vars.get(k, None) != v:
            o_group.vars[k] = v
            resp.changed()
    
    # Delete variables
    vars_to_remove = args.get("remove_vars", [])
    for var_to_remove in vars_to_remove:
        if var_to_remove in o_group.vars:
            del o_group.vars[var_to_remove]
            resp.changed()
    
    #Save group
    if resp.get_changed():
        o_group.save()

    #Set group as child group in parent group
    if "parent_groups" in args:
        parent_groups = list_parser(args.get("parent_groups"))
        o_parent_groups = Group.objects(name__in=parent_groups)
        for o_parent_group in o_parent_groups:
            o_parent_group.update(add_to_set__child_groups=o_group)
            resp.changed()

    return resp.get_response()


@group_pages.route('/groups', methods=['DELETE'])
@authenticate('deleteGroups')
def delete_groups(current_user=None):
    resp = ResponseFormater()
    query_args = dict()
    if "name" in request.args:
        query_args["name__in"] = list_parser(request.args.get("name"))
    else:
        resp.failed(msg='name not defined')
        return resp.get_response()

    o_groups = Group.objects(**query_args)
    if o_groups.count() < 1:
        resp.failed(msg='%s not found' % (request.args.get('name')))
        return resp.get_response()
    s_groups = ','.join(o_groups.scalar('name'))
    o_groups.delete()
    resp.succeed(msg='%s have been deleted' % (s_groups))
    return resp.get_response()
