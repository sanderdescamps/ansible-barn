from http import HTTPStatus
import json
import yaml
import re
import logging, traceback
from flask import request, render_template, jsonify, redirect
from flask_smorest import Blueprint
from flask_login import login_required
from app.models import Host, Group, Node
from app.utils.formater import ResponseBuilder
from webargs.flaskparser import use_kwargs
from marshmallow import fields

from app.utils.schemas import UploadQueryArgsSchema


import_pages = Blueprint('import', __name__)

@import_pages.route('/api/v1/admin/import', methods=['PUT','POST'])
@import_pages.arguments(UploadQueryArgsSchema, location='files', as_kwargs=True)
@import_pages.arguments(UploadQueryArgsSchema, location='json', as_kwargs=True)
@login_required
def put_file_import(**kwargs):

    resp = ResponseBuilder()
    hosts_to_add = []
    groups_to_add = []
    keep_existing_nodes =  kwargs.get("keep")

    for file in kwargs.get("files",[]):
        fileextention = file.filename.split(".")[-1]
        to_add = None
        if fileextention.lower() in ("yaml", "yml"):
            try:
                to_add = yaml.load(file, Loader=yaml.FullLoader)
                resp.log("Successfully loaded %s"%(file.filename))
            except yaml.YAMLError as _:
                return resp.failed(msg="failed to read yaml file: %s"%(file.filename), changed=False, status=HTTPStatus.BAD_REQUEST).get_response()
        elif fileextention.lower() == "json":
            try:
                to_add = json.load(file)
                resp.log("Successfully loaded %s"%(file.filename))
            except json.JSONDecodeError as _:
                return resp.failed(msg="failed to read json file: %s"%(file.filename), changed=False, status=HTTPStatus.BAD_REQUEST).get_response()
        elif fileextention.lower() == "ini":
            try:
                data = file.read().decode('utf-8')
                to_add = _convert_ini(data)
                resp.log("Successfully loaded %s"%(file.filename))
            except Exception:
                return resp.failed(msg="failed to read ini file: %s"%(file.filename), changed=False, status=HTTPStatus.BAD_REQUEST).get_response()
        else:
            return resp.failed("unsupported extention", changed=False, status=HTTPStatus.BAD_REQUEST).get_response()


        if "hosts" in to_add and isinstance(to_add["hosts"], list):
            hosts_to_add.extend(to_add["hosts"])
        if "groups" in to_add and isinstance(to_add["groups"], list):
            groups_to_add.extend(to_add["groups"])
        
        for node in to_add.get("nodes", []):
            if node.get("type", "").lower() == "host":
                hosts_to_add.append(node)
            elif node.get("type", "").lower() == "group":
                groups_to_add.append(node)

    if len(hosts_to_add) > 0 or len(groups_to_add) > 0:
        if not keep_existing_nodes:
            o_nodes_to_delete = Node.objects()
            if o_nodes_to_delete.count() > 0:
                o_nodes_to_delete.delete()
                resp.log("Remove old hosts and groups")
                logging.info("Remove all existing nodes during import")
                resp.changed()
            else:
                logging.info("Keep existing nodes during import")

        # first make sure all nodes exist
        for host in hosts_to_add:
            if host.get("name") and not Host.objects(name=host.get("name")).first():
                Host(name=host.get("name")).save()
        for group in groups_to_add:
            if group.get("name") and not Group.objects(name=group.get("name")).first():
                Group(name=group.get("name")).save()

        for host in hosts_to_add:
            try:
                o_host = Host.from_json(host, append=True)
                o_host.save()
                resp.add_result(o_host)
                resp.changed()
            except Exception:
                logging.error(traceback.format_exc())
                resp.log("Failed to import host %s"%(host.get("name","unknown")))
        for group in groups_to_add:
            try:
                o_group = Group.from_json(group,append=True)
                o_group.save()
                resp.add_result(o_group)
                resp.changed()
            except Exception:
                logging.error(traceback.format_exc())
                resp.log("Failed to import group %s"%(group.get("name","unknown")))
    else:
        resp.failed(msg="No valid hosts or groups in import")

    resp.log("Import completed")
    return resp.get_response()

_COMMENT_MARKERS = frozenset((u';', u'#'))
def _convert_ini(data):

        section_pathern =  re.compile(r'^\[([^:\]\s]+)(?::(\w+))?\]\s*(?:\#.*)?$')

        output_groups = {}
        output_hosts = {}
        groupname = 'ungrouped'
        state = 'hosts'
        
        section_dict = {}


        for line in str(data).splitlines():

            line = line.strip()
            # Skip empty lines and comments
            if not line or line[0] in _COMMENT_MARKERS:
                continue

            m = section_pathern.match(line)
            if m:
                (groupname, state) = m.groups()
                state = state or 'hosts'
            elif line.startswith('[') and line.endswith(']'):
                logging.warning("Invalid section entry: '%s'. Please make sure that there are no spaces" % line + " " +
                                  "in the section entry, and that there are no other invalid characters")
            else:
                section = ":".join((groupname,state))
                if section in section_dict:
                    section_dict[section].append(line)
                else:
                    section_dict[section] = [line]

        hosts_sections = {key:value for key,value in section_dict.items() if key.endswith("hosts")}
        children_sections = {key:value for key,value in section_dict.items() if key.endswith("children")}
        vars_sections = {key:value for key,value in section_dict.items() if key.endswith("vars")}

        for section_title, lines in hosts_sections.items():
            groupname = section_title.split(":")[0]
            group_hosts = []
            for line in lines:
                name = line.strip().split(" ")[0]
                output_hosts[name] = dict(name=name, vars={})
                group_hosts.append(name)

            if groupname != "ungrouped":
                output_groups[groupname] = dict(name=groupname, hosts=group_hosts)
    
        for section_title, lines in children_sections.items():
            groupname = section_title.split(":")[0]
            child_groups = [line.strip().split(" ")[0] for line in lines]
            if groupname not in output_groups: 
                output_groups[groupname] = dict(name=groupname)
            output_groups[groupname]["child_groups"] = child_groups

        return dict(
            hosts=list(output_hosts.values()),
            groups=list(output_groups.values())
        )

