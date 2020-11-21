from flask import request, Blueprint, render_template, jsonify, redirect, url_for
from mongoengine.errors import NotUniqueError
from http import HTTPStatus
from app.models import Node, Host, Group
from app.utils import merge_args_data, list_parser
from app.utils.formater import ResponseFormater
from app.auth import authenticate
from app.pages.nodes import put_nodes
import yaml
import json



upload_pages = Blueprint('upload', __name__)

@upload_pages.route('/upload', methods = ['GET'])
def get_upload_file():
    return render_template('upload.html')

@upload_pages.route('/upload', methods = ['POST'])
@authenticate("guest")
def post_upload_file(current_user=None):
    if "file" in request.files:
        file = request.files['file']
        fileextention = file.filename.split(".")[-1]
        
        to_add = None
        if fileextention.lower() in ("yaml", "yml"):
            to_add = yaml.load(file)
        elif fileextention.lower() == "json":
            to_add = json.load(file)
        else:
            return jsonify(dict(msg="unsuported extention"), status=HTTPStatus.BAD_REQUEST)

        # Create nodes first
        hosts_to_add = to_add.get("hosts",[])
        groups_to_add = to_add.get("groups",[])
        for node in to_add.get("nodes",[]):
            if node.get("type","").lower() == "host":
                hosts_to_add.append(node)
            elif node.get("type","").lower() == "group":
                groups_to_add.append(node)

        for host in hosts_to_add:
            if host.get("name") and not Host.objects(name=host.get("name")):
                Host(name=host.get("name")).save()

        for group in groups_to_add:
            if group.get("name") and not Group.objects(name=group.get("name")):
                Group(name=group.get("name")).save()

        for host in to_add.get("hosts",[]):
            o_host = Host.from_json(host)
            o_host.save()

        for group in to_add.get("groups",[]):
            o_group = Group.from_json(group)
            o_group.save()



        return jsonify(to_add)
    else:
        return redirect('/upload')

