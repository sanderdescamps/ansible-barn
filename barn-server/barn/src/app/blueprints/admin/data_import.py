from http import HTTPStatus
import json
import yaml
import logging
from flask import request, Blueprint, render_template, jsonify, redirect
from flask_login import login_required
from app.models import Host, Group, Node
from app.utils.formater import ResponseFormater


import_pages = Blueprint('import', __name__)

@import_pages.route('/api/v1/admin/import', methods=['PUT','POST'])
@login_required
def put_file_import():
    resp = ResponseFormater()
    hosts_to_add = []
    groups_to_add = []
    logging.debug(request.files.values())
    logging.debug(request.files.keys())
    for file in request.files.values():
        fileextention = file.filename.split(".")[-1]
        to_add = None
        if fileextention.lower() in ("yaml", "yml"):
            try:
                to_add = yaml.load(file, Loader=yaml.FullLoader)
                resp.add_message("Successfully loaded %s"%(file.filename))
            except yaml.YAMLError as _:
                return resp.failed(msg="failed to read yaml file: %s"%(file.filename), changed=False, status=HTTPStatus.BAD_REQUEST).get_response()
        elif fileextention.lower() == "json":
            try:
                to_add = json.load(file)
                resp.add_message("Successfully loaded %s"%(file.filename))
            except json.JSONDecodeError as _:
                return resp.failed(msg="failed to read json file: %s"%(file.filename), changed=False, status=HTTPStatus.BAD_REQUEST).get_response()
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
        o_nodes_to_delete = Node.objects()
        if o_nodes_to_delete.count() > 0:
            o_nodes_to_delete.delete()
            resp.add_message("Remove old hosts and groups")
            resp.changed()

        # first make sure all nodes exist
        for host in hosts_to_add:
            if host.get("name") and not Host.objects(name=host.get("name")):
                Host(name=host.get("name")).save()
        for group in groups_to_add:
            if group.get("name") and not Group.objects(name=group.get("name")):
                Group(name=group.get("name")).save()

        for host in hosts_to_add:
            try:
                o_host = Host.from_json(host)
                o_host.save()
                resp.add_result(o_host)
                resp.changed()
            except Exception as _:
                resp.add_message("Failed to import host %s"%(host.get("name","unknown")))
        for group in groups_to_add:
            try:
                o_group = Group.from_json(group)
                o_group.save()
                resp.add_result(o_group)
                resp.changed()
            except Exception as _:
                resp.add_message("Failed to import group %s"%(group.get("name","unknown")))
    else:
        resp.failed(msg="No valid hosts or groups in import")

    resp.add_message("Import completed")
    return resp.get_response()
