import re
import logging
from flask_smorest import Blueprint
from flask_login import login_required
from mongoengine.errors import NotUniqueError
from app.models import Crate, Host, Group, Node
from app.utils.formater import ResponseBuilder
from app.utils.schemas import BaseResponse, CrateAddSchema, CrateDeleteSchema, CrateQuerySchema, CrateResponse, CrateUpdateSchema


crate_pages = Blueprint('crate', __name__)


@login_required
@crate_pages.route('/api/v1/inventory/crate', methods=['GET'])
@crate_pages.route('/api/v1/inventory/crate/list', methods=['GET'])
@crate_pages.arguments(CrateQuerySchema, location='query', as_kwargs=True)
@crate_pages.response(200, CrateResponse)
def list_crate(**kwargs):
    """List Crates
    """
    resp = ResponseBuilder()
    resp += _get_crate(**kwargs)
    return resp.build()

@login_required
@crate_pages.route('/api/v1/inventory/crate/list', methods=['POST'])
@crate_pages.arguments(CrateQuerySchema, location='json', as_kwargs=True)
@crate_pages.arguments(CrateQuerySchema, location='query', as_kwargs=True)
@crate_pages.response(200, CrateResponse)
def list_crate2(**kwargs):
    """List Crates
    """
    resp = ResponseBuilder()
    resp += _get_crate(**kwargs)
    return resp.build()

@login_required
@crate_pages.route('/api/v1/inventory/crate/add', methods=['POST'])
@crate_pages.route('/api/v1/inventory/crate/add', methods=['PUT'])
@crate_pages.arguments(CrateAddSchema, location='json', as_kwargs=True)
@crate_pages.response(200, CrateResponse)
def add_crate(**kwargs):
    """Add new Crate

    """
    resp = ResponseBuilder()
    resp += _add_crate(**kwargs)
    return resp.build()

@login_required
@crate_pages.route('/api/v1/inventory/crate/update', methods=['POST','PUT'])
@crate_pages.route('/api/v1/inventory/crate', methods=['POST'])
@crate_pages.arguments(CrateUpdateSchema, location='json', as_kwargs=True)
@crate_pages.response(200, BaseResponse)
def update_crate(**kwargs):
    """Change crate"""
    resp = ResponseBuilder()
    
    if "type" in kwargs and not kwargs.get('force'):
        return resp.failed(msg="Type can't be modified").build()

    resp += _modify_crate(**kwargs)
    return resp.build()


@crate_pages.route('/api/v1/inventory/crate/delete', methods=['DELETE'])
@crate_pages.route('/api/v1/inventory/crate', methods=['DELETE'])
@crate_pages.arguments(CrateDeleteSchema, location='query', as_kwargs=True)
@crate_pages.response(200, CrateResponse)
@login_required
def remove_crate(**kwargs):
    """Remove crate"""
    resp = ResponseBuilder()
    resp += _delete_crate(**kwargs)
    return resp.build()


@crate_pages.route('/api/v1/inventory/crate/delete', methods=['POST'])
@crate_pages.arguments(CrateDeleteSchema, location='json', as_kwargs=True)
@crate_pages.response(200, CrateResponse)
@login_required
def remove_crate2(**kwargs):
    """Remove crate"""
    resp = ResponseBuilder()
    resp += _delete_crate(**kwargs)
    return resp.build()

def _get_crate(**kwargs):
    resp = ResponseBuilder()

    query_args = {}
    id = kwargs.get("crate_id")
    if id:
        query_args["crate_id"] = id

    o_crates = Crate.objects(**query_args)

    assigned_to = kwargs.get("assign_to")
    if assigned_to:
        o_assigned_to = list()
        for node_name in assigned_to:
            regex_name = re.compile(r"^{}$".format(
                re.escape(node_name).replace("\*", ".*")))
            o_nodes = Node.objects(name=regex_name)
            if o_nodes:
                o_assigned_to.extend(o_nodes)
        query_args["name__in"] = list(set(o_assigned_to))

    
    if o_crates:
        resp.add_result(o_crates)
    return resp


def _add_crate(**kwargs):
    resp = ResponseBuilder()

    type = kwargs.get("type")
    vars = kwargs.get("vars", {})
    crate = Crate(type=type, vars=vars)
    crate.save()
    resp.log("New crate {} has been created".format(
        crate.get_id())).changed().add_result(crate)
    kwargs["crate_id"] = crate.get_id()

    resp+=_modify_crate(**kwargs)
    return resp


def _modify_crate(**kwargs):
    resp = ResponseBuilder()

    query_args = {}
    if "crate_id" in kwargs:
        query_args["crate_id"] = kwargs.get("crate_id")

    o_crate = Crate.objects(**query_args).first()
    if not o_crate:
        return resp.failed(msg="Crate not found")
    h_crate_original = hash(o_crate)

    variables = kwargs.get("vars")
    if variables is not None:
        for k, v in variables.items():
            if k not in o_crate.vars or o_crate.vars.get(k) != v:
                o_crate.vars[k] = v
                resp.changed().log("Update variable: {}".format(k))

    vars_absent = kwargs.get("vars_absent")
    if vars_absent is not None:
        for k in vars_absent:
            if k in o_crate.vars:
                o_crate.vars.pop(k, None)
                resp.changed().log("Remove variable {}".format(k))
            else:
                resp.log("Variable {} does not exist".format(k))


    assign_to = kwargs.get("assign_to")
    if assign_to:
        for node in assign_to:
            node_type = Node
            if node.startswith("host:"):
                node = node[5:]
                node_type = Host
            elif node.startswith("group:"):
                node = node[6:]
                node_type = Group
            regex_name = re.compile(r"^{}$".format(
                re.escape(node).replace("\*", ".*")))
            o_nodes = node_type.objects(name=regex_name)
            for o_node in o_nodes:
                changed = o_node.subscribe_crate(o_crate)
                if changed:
                    o_node.save()
                    resp.log("Add crate to {}".format(o_node.name)).changed()

    not_assign_to = kwargs.get("not_assign_to")
    if not_assign_to:
        for node in not_assign_to:
            node_type = Node
            if node.startswith("host:"):
                node = node[5:]
                node_type = Host
            elif node.startswith("group:"):
                node = node[6:]
                node_type = Group
            regex_name = re.compile(r"^{}$".format(
                re.escape(node).replace("\*", ".*")))
            o_nodes = node_type.objects(name=regex_name, crates__in=[o_crate])
            for o_node in o_nodes:
                changed = o_node.unsubscribe_crate(o_crate)
                if changed:
                    o_node.save()
                    resp.log("Remove crate from {}".format(o_node.name)).changed()

    if h_crate_original != hash(o_crate):
        o_crate.save()
        resp.changed()
        resp.log("Crate {} has been updated".format(o_crate.get_id()))

    return resp

def _delete_crate(**kwargs):
    resp = ResponseBuilder()

    if "crate_id" not in kwargs and "type" not in kwargs and not kwargs.get("force"):
        return resp.failed(msg="Operation will remove a lot of crates. Use 'force=true' if you are sure you want to continue.")

    query_args = {}
    id = kwargs.get("crate_id")
    if id:
        query_args["crate_id"] = id
    crate_type = kwargs.get("type")
    if crate_type:
        query_args["type"] = crate_type

    o_crates = Crate.objects(**query_args)
    if not kwargs.get("force") and not kwargs.get("multiple") and len(o_crates) > 1:
        return resp.failed(msg="Do you want to remove multiple Crates? Set 'multiple=True' to allow this action.")
    if len(o_crates):
        s_crates = ','.join(o_crates.scalar('crate_id'))
        resp.add_result([o_crate.to_barn_dict() for o_crate in o_crates])
        Node.objects(crates__in=o_crates).update(pull_all__crates=o_crates)
        o_crates.delete()
        resp.succeed(msg='Delete crates %s' % (s_crates), changed=True)
    else:
        resp.succeed(msg='Crate not found')

    return resp
