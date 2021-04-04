import json
import yaml
from flask import request, make_response
from flask_smorest import Blueprint
from flask_login import login_required
from app.models import Host, Group
from app.utils import merge_args_data, remove_empty_fields
from app.utils.schemas import ExportQueryArgsSchema


export_pages = Blueprint('export', __name__)

@export_pages.route('/api/v1/admin/export', methods=['GET'])
@export_pages.arguments(ExportQueryArgsSchema, location='query', as_kwargs=True)
@login_required
def get_export(**kwargs):
    return _get_export(**kwargs)

@export_pages.route('/api/v1/admin/export', methods=['POST'])
@export_pages.arguments(ExportQueryArgsSchema, location='query', as_kwargs=True)
@export_pages.arguments(ExportQueryArgsSchema, location='json', as_kwargs=True)
@login_required
def post_export(**kwargs):
    return _get_export(**kwargs)

def _get_export(**kwargs):
    export_data = dict(hosts=[], groups=[])

    o_hosts = Host.objects()
    for o_host in o_hosts:
        export_data["hosts"].append(o_host.to_barn_dict())

    o_groups = Group.objects()
    for o_group in o_groups:
        export_data["groups"].append(o_group.to_barn_dict())

    if not kwargs.get("full", True):
        export_data = remove_empty_fields(export_data)

    response = None
    if kwargs.get("format") in ("yaml", "yml"):
        response = make_response(
            yaml.dump(yaml.load(json.dumps(export_data)), indent=2))
        response.headers.set('Content-Type', 'text/plain')
    else:
        response = make_response(json.dumps(export_data, indent=2))
        response.headers.set('Content-Type', 'application/json')

    if "file" in kwargs and kwargs.get("file"):
        response.headers.set(
            'Content-Disposition', 'attachment', filename='barn-export.%s' % (kwargs.get("format")))

    return response
