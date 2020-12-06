import json
import yaml
from flask import request, Blueprint, make_response
from flask_login import login_required
from app.models import Host, Group
from app.utils import merge_args_data, remove_empty_fields


export_pages = Blueprint('export', __name__)


@export_pages.route('/api/v1/admin/export', methods=['GET'])
@login_required
def get_export():
    export_data = dict(hosts=[], groups=[])
    args = merge_args_data(request.args, request.get_json(silent=True))

    o_hosts = Host.objects()
    for o_host in o_hosts:
        export_data["hosts"].append(o_host.to_barn_dict())

    o_groups = Group.objects()
    for o_group in o_groups:
        export_data["groups"].append(o_group.to_barn_dict())

    if args.get("full", "").lower() in ("false", "no", "n", "0"):
        export_data = remove_empty_fields(export_data)

    response = None
    if args.get("format") in ("yaml", "yml"):
        response = make_response(
            yaml.dump(yaml.load(json.dumps(export_data)), indent=2))
        response.headers.set('Content-Type', 'text/plain')
    else:
        response = make_response(json.dumps(export_data, indent=2))
        response.headers.set('Content-Type', 'application/json')

    if "file" in args and args.get("file").lower() in ("true", "yes", "y", "1"):
        response.headers.set(
            'Content-Disposition', 'attachment', filename='barn-export.%s' % (args.get("format")))

    return response
