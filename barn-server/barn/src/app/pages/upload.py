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

        for node in to_add.get("nodes",[]):
            o_node = Node.from_json(node)
            o_node.save()

        for host in to_add.get("hosts",[]):
            o_host = Host.from_json(host)
            o_host.save()

        for group in to_add.get("groups",[]):
            o_group = Group.from_json(group)
            o_group.save()



        return jsonify(to_add)
    else:
        return redirect('/upload')

