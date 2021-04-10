import logging
import re
from http import HTTPStatus
from flask_smorest import Blueprint
from flask import request, abort
from mongoengine.errors import NotUniqueError
from flask_login import login_required
from app.models import Group, Host
from app.utils.formater import ResponseBuilder
from app.utils.schemas import GroupPutQueryArgsSchema, GroupQueryArgsSchema, NodeResponse


group_pages = Blueprint('group', __name__)


@group_pages.route('/api/v1/inventory/groups', methods=['GET'])
@group_pages.arguments(GroupQueryArgsSchema, location='query', as_kwargs=True )
@group_pages.response(200, NodeResponse)
@login_required
def get_groups(resp=None, **kwargs):
    return _get_groups(resp=resp, **kwargs)

@group_pages.route('/api/v1/inventory/groups', methods=['POST'])
@group_pages.arguments(GroupQueryArgsSchema, location='query', as_kwargs=True )
@group_pages.arguments(GroupQueryArgsSchema, location='json', as_kwargs=True )
@group_pages.response(200, NodeResponse)
@login_required
def post_groups(resp=None, **kwargs):
    return _get_groups(resp=resp, **kwargs)

def _get_groups(resp=None, **kwargs):
    resp = resp or ResponseBuilder()
    query_args = dict()
    if "name" in kwargs:     
        if kwargs.get("regex",False):
            regex_name = re.compile("^{}$".format(kwargs.get("name").strip(" ").lstrip("^").rstrip("$")))
            query_args["name"] = regex_name
        else:
            regex_name = re.compile(r"^{}$".format(re.escape(kwargs.get("name")).replace("\*",".*")))
            query_args["name"] = regex_name
    o_groups = Group.objects(**query_args)
    resp.add_result(o_groups)
    return resp.build()

@group_pages.route('/api/v1/inventory/groups', methods=['PUT'])
@group_pages.arguments(GroupPutQueryArgsSchema, location='query', as_kwargs=True )
@group_pages.arguments(GroupPutQueryArgsSchema, location='json', as_kwargs=True )
@login_required
def put_groups(resp=None, **kwargs):
    if resp is None:
        resp = ResponseBuilder()

    name = kwargs.get("name", None)
    if name is None:
        abort(400, description="name not defined in request")

    # Create Group
    o_group = Group.objects(name=name).first()
    if o_group is None:
        try:
            query_args = dict(name=name)
            o_group = Group(**query_args)
            resp.succeed(changed=True, status=HTTPStatus.CREATED)
            resp.log("Create group {}".format(name), main=True)
        except NotUniqueError:
            resp.failed(msg='%s already exist' % (name))
            return resp.build()

    if  "child_groups_present" in kwargs:
        for child_group in kwargs.get("child_groups", []):
            o_child_group = Group.objects(name=child_group).first()
            if not o_child_group and kwargs.get('create_groups', True):
                o_child_group = Group(name=child_group)
                o_child_group.save()
                resp.changed()
                resp.log("Create group {}".format(child_group))
            if o_child_group:
                if o_child_group not in o_group.child_groups:
                    o_group.child_groups.append(o_child_group)
                    resp.changed()
                    resp.log(
                        "Add {} group as child-group".format(child_group))
            else:
                resp.log(
                    "Can't add {} as child group. Group does not exist.")

    if "child_groups_set" in kwargs:
        o_child_groups = []
        for child_group in kwargs.get("child_groups_set", []):
            o_child_group = Group.objects(name=child_group).first()
            if not o_child_group and kwargs.get('create_groups', True):
                o_child_group = Group(name=child_group)
                o_child_group.save()
                resp.changed()
                resp.log("Create group {}")
            if o_child_group:
                o_child_groups.append(o_child_group)
            else:
                resp.log(
                    "Can't set {} as child group. Group does not exist.")

        if set(o_group.child_groups) != set(o_child_groups):
            o_group.child_groups = o_child_groups
            resp.changed()
            if len(o_child_groups) == 0:
                resp.log(
                    "Remove all child-groups from {}".format(o_group.name))
            else:
                resp.log(
                    "Set {} as child-group of {}".format(','.join([cg.name for cg in o_child_groups]), o_group.name))

    if "child_groups_absent" in kwargs:
        for child_group in kwargs.get("child_groups_absent"):
            o_child_group = Group.objects(name=child_group).first()
            if o_child_group is None:
                resp.log("{} group does not exist".format(child_group))
            elif o_child_group in o_group.child_groups:
                o_group.child_groups.remove(o_child_group)
                resp.changed()
                resp.log(
                    "Remove {} from child-groups".format(child_group))
            else:
                resp.log(
                    "{} is not a child-group of {}".format(child_group, name))

    if "hosts_present" in kwargs:
        hosts = kwargs.get("hosts_present", [])

        o_hosts = Host.objects(name__in=hosts)
        hosts_not_found = list(
            set(hosts).difference(set(o_hosts.scalar('name'))))
        if len(hosts_not_found) > 0:
            resp.log("Hosts not found: {}".format(
                ", ".join(hosts_not_found)))
        o_hosts_to_add = set(o_hosts).difference(o_group["hosts"])
        if len(o_hosts_to_add) > 0:
            o_group["hosts"].extend(o_hosts_to_add)
            resp.changed()

            resp.log("Add {} to hosts".format(
                ",".join(map(lambda h: h.name, o_hosts_to_add))))
    if "hosts_set" in kwargs:
        hosts = kwargs.get("hosts_set")

        o_hosts = Host.objects(name__in=hosts)
        hosts_not_found = list(
            set(hosts).difference(set(o_hosts.scalar('name'))))
        if len(hosts_not_found) > 0:
            resp.log("Hosts not found: {}".format(
                ", ".join(hosts_not_found)))
        if set(o_group["hosts"]) != set(o_hosts):
            o_group["hosts"] = list(o_hosts)
            resp.changed()
            resp.log("Set {} to hosts".format(
                ",".join(o_hosts_to_add.scalar('name'))))
    if "hosts_absent" in kwargs:
        hosts = kwargs.get("hosts_absent")
        o_hosts = Host.objects(name__in=hosts)
        o_hosts_to_remove = set(o_hosts).union(set(o_group["hosts"]))
        for o_host in o_hosts_to_remove:
            o_group["hosts"].remove(o_host)
            resp.changed()
            resp.log("Remove {} from hosts".format(o_host.get("name")))

    # Set variables
    barn_vars = kwargs.get("vars", {})
    for k, v in barn_vars.items():
        if o_group.vars.get(k, None) != v:
            o_group.vars[k] = v
            resp.changed()

    # Delete variables
    vars_to_remove = kwargs.get("vars_absent", [])
    for var_to_remove in vars_to_remove:
        if var_to_remove in o_group.vars:
            del o_group.vars[var_to_remove]
            resp.changed()

    # Save group
    if resp.get_changed():
        o_group.save()

    parent_groups_present = kwargs.get("parent_groups_present", [])
    parent_groups_set = kwargs.get("parent_groups_set", [])
    parent_groups_absent = kwargs.get("parent_groups_absent", [])
    used_groups_list = parent_groups_present + parent_groups_set
    used_groups_list = list(set(used_groups_list))

    # Add groups who do not exist
    for g in used_groups_list:
        if Group.objects(name=g).first() is None:
            if kwargs.get('create_groups', True):
                Group(name=g).save()
                resp.log("Create group {}".format(g))
                resp.changed()
            else:
                resp.log("{} group does not exist.".format(g))

    if "parent_groups_present" in kwargs:
        o_parent_groups_to_add = Group.objects(
            name__in=parent_groups_present, child_groups__nin=[o_group])

        if len(o_parent_groups_to_add) > 0:
            o_parent_groups_to_add.update(add_to_set__child_groups=o_group)
            resp.changed()
            s_parent_groups_to_add = ",".join(
                [str(g) for g in o_parent_groups_to_add])
            resp.log(
                "Add {} to child-groups of {}".format(o_group.name, s_parent_groups_to_add))

    if "parent_groups_set" in kwargs:
        o_parent_groups_to_add = Group.objects(
            name__in=parent_groups_set, child_groups__nin=[o_group])
        if len(o_parent_groups_to_add) > 0:
            o_parent_groups_to_add.update(add_to_set__child_groups=o_group)
            resp.changed()
            s_parent_groups_to_add = ",".join(
                [str(g) for g in o_parent_groups_to_add])
            resp.log(
                "Add {} to child-groups of {}".format(o_group.name, s_parent_groups_to_add))

        o_parent_groups_to_remove = Group.objects(
            name__nin=parent_groups_set, child_groups__in=[o_group])
        if len(o_parent_groups_to_remove) > 0:
            o_parent_groups_to_remove.update(pull__child_groups=o_group)
            resp.changed()
            s_parent_groups_to_remove = ",".join(
                [str(g) for g in o_parent_groups_to_remove])
            resp.log(
                "Remove {} from child-groups of {}".format(o_group.name, s_parent_groups_to_remove))

    if "parent_groups_absent" in kwargs:
        o_parent_groups_to_remove = Group.objects(
            name__in=parent_groups_absent, child_groups__in=[o_group])
        if len(o_parent_groups_to_remove) > 0:
            o_parent_groups_to_remove.update(pull__child_groups=o_group)
            resp.changed()
            s_parent_groups_to_remove = ",".join(
                [str(g) for g in o_parent_groups_to_remove])
            resp.log(
                "Remove {} from child-groups of {}".format(o_group.name, s_parent_groups_to_remove))

    return resp.build()


@group_pages.route('/api/v1/inventory/groups', methods=['DELETE'])
@group_pages.arguments(GroupQueryArgsSchema, location='query', as_kwargs=True )
@group_pages.arguments(GroupQueryArgsSchema, location='json', as_kwargs=True )
@group_pages.response(200, NodeResponse)
@login_required
def delete_groups(**kwargs):
    resp = ResponseBuilder()
    query_args = dict()
    if "name" in kwargs:     
        if kwargs.get("regex",False):
            regex_name = re.compile("^{}$".format(kwargs.get("name").strip(" ").lstrip("^").rstrip("$")))
            query_args["name"] = regex_name
        else:
            regex_name = re.compile(r"^{}$".format(re.escape(kwargs.get("name")).replace("\*",".*")))
            query_args["name"] = regex_name
    else:
        resp.failed(msg='Name not defined')
        return resp.build()

    o_groups = Group.objects(**query_args)
    logging.getLogger().info("remove groups: %s", ','.join(o_groups.scalar('name')))
    Group.objects(child_groups__in=o_groups).update(
        pull_all__child_groups=o_groups)

    if o_groups.count() < 1:
        resp.failed(msg='%s not found' % (kwargs.get('name')))
        return resp.build()
    s_groups = ','.join(o_groups.scalar('name'))
    o_groups.delete()

    resp.succeed(msg='%s have been deleted' % (s_groups))
    return resp.build()
