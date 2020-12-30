import logging
from http import HTTPStatus
from flask import Blueprint, request, abort
from mongoengine.errors import NotUniqueError
from flask_login import login_required
from app.utils import list_parser, merge_args_data
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

    # Create Group
    o_group = Group.objects(name=name).first()
    if o_group is None:
        try:
            query_args = dict(name=name)
            o_group = Group(**query_args)
            resp.succeed(changed=True, status=HTTPStatus.CREATED)
            resp.set_main_message("Create group {}".format(name))
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
                    resp.add_message(
                        "Add {} group as child-group".format(child_group))
            else:
                resp.add_message(
                    "Can't add {} as child group. Group does not exist.")

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
                resp.add_message(
                    "Can't set {} as child group. Group does not exist.")

        if set(o_group.child_groups) != set(o_child_groups):
            o_group.child_groups = o_child_groups
            resp.changed()
            if len(o_child_groups) == 0:
                resp.add_message(
                    "Remove all child-groups from {}".format(o_group.name))
            else:
                resp.add_message(
                    "Set {} as child-group of {}".format(','.join([cg.name for cg in o_child_groups]), o_group.name))

    if "child_groups_absent" in args:
        for child_group in list_parser(args.get("child_groups_absent")):
            o_child_group = Group.objects(name=child_group).first()
            if o_child_group is None:
                resp.add_message("{} group does not exist".format(child_group))
            elif o_child_group in o_group.child_groups:
                o_group.child_groups.remove(o_child_group)
                resp.changed()
                resp.add_message(
                    "Remove {} from child-groups".format(child_group))
            else:
                resp.add_message(
                    "{} is not a child-group of {}".format(child_group, name))

    if "hosts" in args:
        hosts = list_parser(args.get("hosts")) or list_parser(
            args.get("hosts_present", []))

        o_hosts = Host.objects(name__in=hosts)
        hosts_not_found = list(
            set(hosts).difference(set(o_hosts.scalar('name'))))
        if len(hosts_not_found) > 0:
            resp.add_message("Hosts not found: {}".format(
                ",".join(hosts_not_found)))
        o_hosts_to_add = set(o_hosts).difference(o_group["hosts"])
        if len(o_hosts_to_add) > 0:
            o_group["hosts"].extend(o_hosts_to_add)
            resp.changed()

            resp.add_message("Add {} to hosts".format(
                ",".join(map(lambda h: h.name, o_hosts_to_add))))
    if "hosts_set" in args:
        hosts = list_parser(args.get("hosts_set"))

        o_hosts = Host.objects(name__in=hosts)
        hosts_not_found = list(
            set(hosts).difference(set(o_hosts.scalar('name'))))
        if len(hosts_not_found) > 0:
            resp.add_message("Hosts not found: {}".format(
                ",".join(hosts_not_found)))
        if set(o_group.get("hosts")) != set(o_hosts):
            o_group["hosts"] = list(o_hosts)
            resp.changed()
            resp.add_message("Set {} to hosts".format(
                ",".join(o_hosts_to_add.scalar('name'))))
    if "hosts_absent" in args:
        hosts = list_parser(args.get("hosts_absent"))
        o_hosts = Host.objects(name__in=hosts)
        o_hosts_to_remove = set(o_hosts).union(set(o_group["hosts"]))
        for o_host in o_hosts_to_remove:
            o_group["hosts"].remove(o_host)
            resp.changed()
            resp.add_message("Remove {} from hosts".format(o_host.get("name")))

    # Set variables
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

    # Save group
    if resp.get_changed():
        o_group.save()

    parent_groups_present = list_parser(
        args.get("parent_groups", args.get("parent_groups_present", [])))
    parent_groups_set = list_parser(args.get("parent_groups_set", []))
    parent_groups_absent = list_parser(args.get("parent_groups_absent", []))
    used_groups_list = parent_groups_present + parent_groups_set
    used_groups_list = list(set(used_groups_list))
    logging.debug("list used groups: %s", ",".join(used_groups_list))

    # Add groups who do not exist
    for g in used_groups_list:
        if Group.objects(name=g).first() is None:
            if args.get('create_groups', True):
                Group(name=g).save()
                resp.add_message("Create group {}".format(g))
                resp.changed()
            else:
                resp.add_message("{} group does not exist.".format(g))

    if "parent_groups" in args or "parent_groups_present" in args:
        o_parent_groups_to_add = Group.objects(
            name__in=parent_groups_present, child_groups__nin=[o_group])

        if len(o_parent_groups_to_add) > 0:
            o_parent_groups_to_add.update(add_to_set__child_groups=o_group)
            resp.changed()
            s_parent_groups_to_add = ",".join(
                [str(g) for g in o_parent_groups_to_add])
            resp.add_message(
                "Add {} to child-groups of {}".format(o_group.name, s_parent_groups_to_add))

    if "parent_groups_set" in args:
        o_parent_groups_to_add = Group.objects(
            name__in=parent_groups_set, child_groups__nin=[o_group])
        if len(o_parent_groups_to_add) > 0:
            o_parent_groups_to_add.update(add_to_set__child_groups=o_group)
            resp.changed()
            s_parent_groups_to_add = ",".join(
                [str(g) for g in o_parent_groups_to_add])
            resp.add_message(
                "Add {} to child-groups of {}".format(o_group.name, s_parent_groups_to_add))

        o_parent_groups_to_remove = Group.objects(
            name__nin=parent_groups_set, child_groups__in=[o_group])
        if len(o_parent_groups_to_remove) > 0:
            o_parent_groups_to_remove.update(pull__child_groups=o_group)
            resp.changed()
            s_parent_groups_to_remove = ",".join(
                [str(g) for g in o_parent_groups_to_remove])
            resp.add_message(
                "Remove {} from child-groups of {}".format(o_group.name, s_parent_groups_to_remove))

    if "parent_groups_absent" in args:
        o_parent_groups_to_remove = Group.objects(
            name__in=parent_groups_absent, child_groups__in=[o_group])
        if len(o_parent_groups_to_remove) > 0:
            o_parent_groups_to_remove.update(pull__child_groups=o_group)
            resp.changed()
            s_parent_groups_to_remove = ",".join(
                [str(g) for g in o_parent_groups_to_remove])
            resp.add_message(
                "Remove {} from child-groups of {}".format(o_group.name, s_parent_groups_to_remove))

    return resp.get_response()


@group_pages.route('/api/v1/inventory/groups', methods=['DELETE'])
@login_required
def delete_groups():
    resp = ResponseFormater()
    args = merge_args_data(request.args, request.get_json(silent=True))
    query_args = dict()
    if "name" in args:
        query_args["name__in"] = list_parser(args.get("name"))
    else:
        resp.failed(msg='name not defined')
        return resp.get_response()

    o_groups = Group.objects(**query_args)
    logging.getLogger().info("remove groups: %s", ','.join(o_groups.scalar('name')))
    Group.objects(child_groups__in=o_groups).update(
        pull_all__child_groups=o_groups)

    if o_groups.count() < 1:
        resp.failed(msg='%s not found' % (args.get('name')))
        return resp.get_response()
    s_groups = ','.join(o_groups.scalar('name'))
    o_groups.delete()

    resp.succeed(msg='%s have been deleted' % (s_groups))
    return resp.get_response()
