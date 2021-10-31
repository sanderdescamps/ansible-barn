from http import HTTPStatus
try:
    import ujson as json
except ImportError:
    import json
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
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

doc_parameters=[
    {
        "in": "query",
        "name": "full",
        "required": False,
        "description": "Keep empty fields",
        "schema": dict(
            type="boolean"
        )
    }
]

@import_pages.route('/api/v1/admin/import', methods=['PUT','POST'])
@import_pages.arguments(UploadQueryArgsSchema, location='files', as_kwargs=True)
@import_pages.arguments(UploadQueryArgsSchema, location='json', as_kwargs=True)
@import_pages.doc(parameters=doc_parameters)
@login_required
def put_file_import(**kwargs):
    """Import data

    Upload data files at [/upload](/upload)

    """

    resp = ResponseBuilder()
    hosts_to_add = []
    groups_to_add = []
    keep_existing_nodes =  kwargs.get("keep")

    for file in kwargs.get("files",[]):
        fileextention = file.filename.split(".")[-1]
        to_add = None
        if fileextention.lower() in ("yaml", "yml"):
            try:
                to_add = yaml.load(file, Loader=Loader)
                resp.log("Successfully loaded %s"%(file.filename))
            except yaml.YAMLError as _:
                return resp.failed(msg="failed to read yaml file: %s"%(file.filename), changed=False, status=HTTPStatus.BAD_REQUEST).build()
        elif fileextention.lower() == "json":
            try:
                to_add = json.load(file)
                resp.log("Successfully loaded %s"%(file.filename))
            except json.JSONDecodeError as _:
                return resp.failed(msg="failed to read json file: %s"%(file.filename), changed=False, status=HTTPStatus.BAD_REQUEST).build()
        elif fileextention.lower() == "ini":
            try:
                data = file.read().decode('utf-8')
                to_add = _convert_ini(data)
                resp.log("Successfully loaded %s"%(file.filename))
            except Exception:
                return resp.failed(msg="failed to read ini file: %s"%(file.filename), changed=False, status=HTTPStatus.BAD_REQUEST).build()
        else:
            return resp.failed("unsupported extention", changed=False, status=HTTPStatus.BAD_REQUEST).build()


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
    return resp.build()

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
                variables = _extract_variables(" ".join(line.strip().split(" ")[1:]))
                output_hosts[name] = dict(name=name, vars=variables)
                group_hosts.append(name)

            if groupname != "ungrouped":
                output_groups[groupname] = dict(name=groupname, hosts=group_hosts)


        for section_title, lines in children_sections.items():
            groupname = section_title.split(":")[0]
            child_groups = [line.strip().split(" ")[0] for line in lines]
            if groupname not in output_groups: 
                output_groups[groupname] = dict(name=groupname)
            output_groups[groupname]["child_groups"] = child_groups

        for section_title, lines in vars_sections.items():
            entity_name = section_title.split(":")[0]
            variables = {}
            for line in lines:
                variables.update(_extract_variables(line))
            
            if entity_name in output_groups:
                current_vars = output_groups[entity_name].get("vars",{})
                current_vars.update(variables)
                output_groups[entity_name]["vars"] = current_vars
            elif entity_name in output_hosts:
                current_vars = output_hosts[entity_name].get("vars",{})
                current_vars.update(variables)
                output_hosts[entity_name]["vars"] = current_vars
            elif entity_name == "all":
                output_groups["all"] = dict(name="all", vars=variables)

        return dict(
            hosts=list(output_hosts.values()),
            groups=list(output_groups.values())
        )

def _extract_variables(line):
    line = line.split('#')[0]
    properties = {}
    match = re.findall(r"(\w+) *= *\"(.*?)\"", line)
    if match:
        for m in match:
            properties[m[0]] = m[1]

    match = re.findall(r"(\w+) *= *\'(.*?)\'", line)
    if match:
        for m in match:
            properties[m[0]] = m[1]
    
    match = re.findall(r"(\w+) *= *([^ \"\']+)", line)
    if match:
        for m in match:
            properties[m[0]] = m[1]

    return properties

