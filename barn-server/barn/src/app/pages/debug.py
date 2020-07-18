from flask import Blueprint, jsonify, current_app
from app.models import Group, Role, Host, User
from app.auth import authenticate
from app.config import ConfigLoader

debug_pages = Blueprint('debug', __name__)


@debug_pages.route('/init', methods=['PUT'])
@authenticate("guest")
def init(current_user=None):
    Role.objects(name__not__iexact="admin").delete()
    Role(name="admin", description="Allow anything")
    Role(name="addHost", description="Add a host to the inventory").save()
    Role(name="addGroup", description="Add a group to the inventory").save()
    Role(name="readOnly", description="Read access on inventory").save()
    Role(name="query", description="Read access on inventory").save()

    User.objects(name__not__iexact=current_app.config.get('BARN_CONFIG').get_barn_config().get("barn_init_admin_user")).delete()
    user_1 = User(name="Sander Descamps", username="sdescamps",
                  password="testpassword", roles=["admin"])
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
