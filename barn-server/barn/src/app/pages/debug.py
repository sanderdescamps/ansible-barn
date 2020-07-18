from flask import Blueprint, jsonify
from app.models import Group, Role, Host, User
from app.auth import authenticate

debug_pages = Blueprint('debug', __name__)


@debug_pages.route('/init', methods=['PUT'])
@authenticate("guest")
def init(current_user=None):
    Role.objects().delete()
    r_admin = Role(name="Admin", description="Allow anything")
    r_admin.save()
    Role(name="AddHost", description="Add a host to the inventory").save()
    Role(name="AddGroup", description="Add a group to the inventory").save()
    Role(name="ReadOnly", description="Read access on inventory").save()
    Role(name="Query", description="Read access on inventory").save()

    User.objects().delete()
    user_1 = User(name="Sander Descamps", username="sdescamps",
                  password="testpassword")
    user_1.roles.append(r_admin)
    user_1.save()

    Host.objects().delete()
    h_srvplex01 = Host(name="srvplex01.myhomecloud.be")
    h_srvplex01.save()
    h_srvdns01 = Host(name="srvdns01.myhomecloud.be")
    h_srvdns01.save()
    h_srvdns02 = Host(name="srvdns02.myhomecloud.be").save()
    h_srvdns02.save()

    Group.objects().delete()
    g_dns_servers = Group(name="dns_servers")
    g_dns_servers.hosts.append(h_srvdns01)
    g_dns_servers.hosts.append(h_srvdns02)
    g_dns_servers.save()
    g_all_servers = Group(name="all_servers")
    g_all_servers.child_groups.append(g_dns_servers)
    g_all_servers.hosts.append(h_srvplex01)
    g_all_servers.save()
    return jsonify({'message': 'Database has been reseted'})


@debug_pages.route('/flush', methods=['DELETE'])
@authenticate("admin")
def flush(current_user=None):
    Host.objects().delete()
    Group.objects().delete()
    return jsonify({'message': 'Database has been flushed'})
