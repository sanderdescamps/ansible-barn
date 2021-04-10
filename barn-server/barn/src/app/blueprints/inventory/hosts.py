import re
import logging
from flask_smorest import Blueprint
from flask_login import login_required
from mongoengine.errors import NotUniqueError
from http import HTTPStatus
from app.models import Host, Group
from app.utils import list_parser, boolean_parser
from app.utils.formater import ResponseBuilder
from app.utils.schemas import BaseResponse, HostQueryArgsSchema, NodeResponse, HostPutQueryArgsSchema

host_pages = Blueprint('host', __name__)


@host_pages.route('/api/v1/inventory/hosts', methods=['GET'])
@host_pages.arguments(HostQueryArgsSchema, location='query', as_kwargs=True)
@host_pages.response(200, NodeResponse)
@login_required
def get_hosts(resp=None, **kwargs):
    """List of hosts"""
    return _get_hosts(resp=resp, **kwargs)


@host_pages.route('/api/v1/inventory/hosts', methods=['POST'])
@host_pages.arguments(HostQueryArgsSchema, location='query', as_kwargs=True)
@host_pages.arguments(HostQueryArgsSchema, location='json', as_kwargs=True)
@host_pages.response(200, NodeResponse)
@login_required
def post_hosts(resp=None, **kwargs):
    return _get_hosts(resp=resp, **kwargs)


def _get_hosts(resp=None, **kwargs):
    """List of hosts"""
    resp = resp or ResponseBuilder()

    query_args = dict()
    if "name" in kwargs:
        if boolean_parser(kwargs.get("regex", False)):
            regex_name = re.compile("^{}$".format(
                kwargs.get("name").strip(" ").lstrip("^").rstrip("$")))
            query_args["name"] = regex_name
        else:
            regex_name = re.compile(r"^{}$".format(
                re.escape(kwargs.get("name")).replace("\*", ".*")))
            query_args["name"] = regex_name
    o_hosts = Host.objects(**query_args)
    if o_hosts.count() < 1:
        log_name = "RegExp({})".format(kwargs.get('name')) if boolean_parser(
            kwargs.get("regex", False)) else kwargs.get('name')
        resp.succeed(msg='No hosts found for {}'.format(log_name))
    resp.add_result(o_hosts)
    return resp.build()


@host_pages.route('/api/v1/inventory/hosts', defaults={'action': "present"}, methods=['PUT'])
@host_pages.route('/api/v1/inventory/hosts/<action>', methods=['PUT'])
@host_pages.arguments(HostPutQueryArgsSchema, location='json', as_kwargs=True)
@host_pages.response(200, BaseResponse)
@login_required
def put_hosts(action="present", resp=None, **kwargs):
    """Modify host"""
    resp = resp or ResponseBuilder()

    name = kwargs.get("name", None)
    if name is None:
        resp.failed(msg='name not defined')
        return resp.build()

    # Create Host
    o_host = Host.objects(name=name).first()
    if o_host is not None and action == "add":
        resp.failed(msg='%s already exist' % (kwargs.get("name")))
        return resp.build()
    elif o_host is None:
        if action == "update":
            resp.failed(msg='Host not found: %s Does not exist' %
                        (kwargs.get("name")))
            return resp.build()
        else:
            try:
                o_host = Host(name=name)
                resp.succeed(changed=True, msg="Create host {}".format(
                    name), status=HTTPStatus.CREATED)
            except NotUniqueError:
                resp.failed(msg='%s already exist' % (kwargs.get("name")))
                return resp.build()

    # Set variables
    barn_vars = kwargs.get("vars", {})
    if action == "set" and barn_vars != o_host.vars:
        o_host.vars = {}
        resp.changed()
        resp.log("Reset host variables")

    for k, v in barn_vars.items():
        if o_host.vars.get(k, None) != v:
            o_host.vars[k] = v
            resp.changed()
            resp.log("Change variable: {}".format(k))

    # Delete variables
    if action != "add":
        vars_to_remove = kwargs.get("vars_absent", [])
        for var_to_remove in vars_to_remove:
            if var_to_remove in o_host.vars:
                del o_host.vars[var_to_remove]
                resp.log("Remove variable: {}".format(var_to_remove))
                resp.changed()

    # Save Host
    if resp.get_changed():
        o_host.save()

    # Add host to group
    o_groups_remove_list = []
    o_groups_add_list = []
    if kwargs.get("groups_present", False):
        groups = list_parser(kwargs.get("groups_present"))
        for group in groups:
            o_group = Group.objects(name=group).first()
            if not o_group and kwargs.get('create_groups', True):
                o_group = Group(name=group)
                resp.changed()
                resp.log("Create {} group".format(group))
            if o_group:
                o_groups_add_list.append(o_group)
    if kwargs.get("groups_set", False) and not any(k in kwargs for k in ("groups_present", "groups_absent")):
        groups = list_parser(kwargs.get("groups_set"))

        o_groups_remove = Group.objects(
            name__not__in=groups, hosts__in=[o_host])
        for g in o_groups_remove:
            o_groups_remove_list.append(g)

        for group in groups:
            o_group = Group.objects(name=group).first()
            if not o_group and kwargs.get('create_groups', True):
                o_group = Group(name=group)
            if o_group:
                o_groups_add_list.append(o_group)
    if kwargs.get("groups_absent", False):
        groups = list_parser(kwargs.get("groups_absent"))
        o_groups_remove = Group.objects(name__in=groups)
        for g in o_groups_remove:
            o_groups_remove_list.append(g)
    for g in list(set(o_groups_remove_list)):
        if o_host in g.hosts:
            g.hosts.remove(o_host)
            resp.log("Remove {} from {} group".format(name, g.name))
            g.save()
            resp.changed()
    for g in list(set(o_groups_add_list)):
        if o_host not in g.hosts:
            g.hosts.append(o_host)
            resp.log("Add {} into {} group".format(name, g.name))
            g.save()
            resp.changed()

    return resp.build()


@host_pages.route('/api/v1/inventory/hosts', methods=['DELETE'])
@login_required
@host_pages.arguments(HostQueryArgsSchema, location='query', as_kwargs=True)
@host_pages.arguments(HostQueryArgsSchema, location='json', as_kwargs=True)
@host_pages.response(200, BaseResponse)
def delete_hosts(**kwargs):
    """Delete host or list of hosts"""
    resp = ResponseBuilder()
    query_args = dict()
    if "name" in kwargs:
        names = list_parser(kwargs.get("name"))
        if boolean_parser(kwargs.get("regex", False)):
            regex_names = [re.compile("^{}$".format(
                n.strip(" ").lstrip("^").rstrip("$"))) for n in names]
            query_args["name__in"] = regex_names
        else:
            regex_names = [re.compile(r"^{}$".format(
                re.escape(n).replace("\*", ".*"))) for n in names]
            query_args["name__in"] = regex_names
    else:
        resp.failed(msg='Name not defined')
        return resp.build()

    o_hosts = Host.objects(**query_args)

    if o_hosts.count() < 1:
        log_name = "RegExp({})".format(kwargs.get('name')) if boolean_parser(
            kwargs.get("regex", False)) else kwargs.get('name')
        resp.failed(msg='No hosts found for {}'.format(log_name))
    else:
        # Remove host from all groups where the host is used
        Group.objects(hosts__in=o_hosts).update(pull_all__hosts=o_hosts)
        s_hosts = ','.join(o_hosts.scalar('name'))
        o_hosts.delete()
        resp.succeed(msg='Delete host %s' % (s_hosts), changed=True)
    return resp.build()
