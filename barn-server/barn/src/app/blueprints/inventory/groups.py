from http import HTTPStatus
from flask import Blueprint, request, abort
from mongoengine.errors import NotUniqueError
from app.utils import list_parser, merge_args_data
from flask_login import login_required
from app.models import Group, Host
from app.utils.formater import ResponseFormater


group_pages = Blueprint('group', __name__)


@group_pages.route('/api/v1/inventory/groups', methods=['GET'])
@login_required
def get_groups(resp=None):
    if resp is None:
        resp = ResponseFormater()
    args = request.args

    query_args = dict()
    if "name" in args:
        query_args["name"] = args.get("name")
    o_groups = Group.objects(**query_args)
    resp.add_result(o_groups)
    return resp.get_response()

@group_pages.route('/api/v1/inventory/groups', methods=['POST'])
@login_required
def post_groups(resp=None):
    if resp is None:
        resp = ResponseFormater()
    data = request.get_json(silent=True)

    query_args = dict()
    if "name" in data:
        query_args["name"] = data.get("name")
    o_groups = Group.objects(**query_args)
    resp.add_result(o_groups)
    return resp.get_response()

@group_pages.route('/api/v1/inventory/groups', methods=['PUT'])
@login_required
def put_groups(resp=None):
    if resp is None:
        resp = ResponseFormater()
    args = merge_args_data(request.args, request.get_json(silent=True))

    name = args.get("name", None)
    if name is None:
        abort(400, description="name not defined in request")

    #Create Group
    o_group = Group.objects(name=name).first()
    if o_group is None:
        try:
            query_args = dict(name=name)
            o_group = Group(**query_args)
            resp.succeed(changed=True, status=HTTPStatus.CREATED)
            resp.set_main_message(msg="Create group {}".format(name))
        except NotUniqueError:
            resp.failed(msg='%s already exist' % (name))
            return resp.get_response()
    
    if "child_groups" in args or "child_groups_present" in args:
        child_groups = []
        child_groups.extend(list_parser(args.get("child_groups", [])))
        child_groups.extend(list_parser(args.get("child_groups_present", [])))
        child_groups = list(set(child_groups))

        for child_group in child_groups:
            o_child_group = Group.objects(name=child_group).first()
            if not o_child_group and args.get('create_groups', True):
                o_child_group = Group(name=child_group)
                o_child_group.save()
                resp.changed()
                resp.add_message("Create group {}".format(child_group))
            if o_child_group:
                if o_child_group not in o_group.child_groups:
                    o_group.child_groups.append(o_child_group)
                    resp.changed()
                    resp.add_message("Add {} group as child-group".format(child_group))
            else:
                resp.add_message("Can't add {} as child group. Group does not exist.")

    if "child_groups_set" in args:
        o_child_groups = []
        for child_group in list_parser(args.get("child_groups_set", [])):
            o_child_group = Group.objects(name=child_group).first()
            if not o_child_group and args.get('create_groups', True):
                o_child_group = Group(name=child_group)
                o_child_group.save()
                resp.changed()
                resp.add_message("Create group {}")
            if o_child_group:
                o_child_groups.append(o_child_group)
            else:
                resp.add_message("Can't set {} as child group. Group does not exist.")

        if set(o_group.child_groups) - set(o_child_groups) != set():
            o_group.child_groups = o_child_groups
            resp.changed()
            resp.add_message("Set child-groups to {}".format(','.join([cg.name for cg in o_child_groups])))

    if "child_groups_absent" in args:
        for child_group in list_parser(args.get("child_groups_absent")):
            o_child_group = Group.objects(name=child_group).first()
            if o_child_group is None:
                resp.add_message("{} group does not exist".format(child_group))
            elif o_child_group in o_group.child_groups:
                o_group.child_groups.remove(o_child_group)
                resp.changed()
                resp.add_message("Remove {} from child-groups".format(child_group))
            else:
                resp.add_message("{} is not a child-group of {}".format(child_group, name))

    
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
    vars_to_remove = args.get("vars_absent", [])
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


@group_pages.route('/api/v1/inventory/groups', methods=['DELETE'])
@login_required
def delete_groups():
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
