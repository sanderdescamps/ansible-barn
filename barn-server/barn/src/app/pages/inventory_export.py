from flask import jsonify, Blueprint
from app.models import Host, Group
from app.auth import authenticate

inventory_pages = Blueprint('inventory', __name__)


@inventory_pages.route('/api/v1/ansible_inventory', methods=['GET'])
@authenticate("guest")
def get_ansible_inventory_file(current_user=None):
    o_hosts = Host.objects()
    d_hosts = {}
    for host in o_hosts:
        d_hosts[host.name] = host.vars

    o_groups = Group.objects()
    d_groups = {}
    for group in o_groups:
        d_groups[group.name] = dict(vars=group.vars, hosts={}, children={})
        if len(group.hosts) > 0:
            d_groups[group.name]["hosts"] = {h.name:None for h in group.hosts}

        if len(group.child_groups) > 0:
            d_groups[group.name]["children"] = {g.name:None for g in group.child_groups}

    result = dict(all=dict(hosts=d_hosts, children=d_groups))
    return jsonify(result)
    