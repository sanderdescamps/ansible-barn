import logging
from flask import jsonify, current_app
from flask_login import login_required
from webargs import fields
from app.models import Group, Host, User
from app.auth import admin_permission
from app.utils.formater import ResponseBuilder
from app.utils.schemas import BaseResponse
from flask_smorest import Blueprint



debug_pages = Blueprint('debug', __name__)



@debug_pages.route('/init', methods=['PUT', 'GET'])
@login_required
def init():
    # Role.objects(name__not__iexact="admin").delete()
    # Role(name="admin", description="Allow anything")
    # Role(name="addHost", description="Add a host to the inventory").save()
    # Role(name="addGroup", description="Add a group to the inventory").save()
    # Role(name="readOnly", description="Read access on inventory").save()
    # Role(name="query", description="Read access on inventory").save()

    User.objects(name__not__iexact=current_app.config.get(
        'BARN_CONFIG').get("barn_init_admin_user")).delete()
    user_1 = User(name="Sander Descamps", username="sdescamps",
                  password="testpassword", admin=True, roles=["test"])
    user_1.save()

    Host.objects().delete()
    h_srvplex01 = Host(name="srvplex01.myhomecloud.be")
    h_srvplex01.save()
    h_srvdns01 = Host(name="srvdns01.myhomecloud.be", vars=dict(
        deploytime="today", env_environment="staging"))
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
@debug_pages.response(200, BaseResponse)
@login_required
def flush():
    Host.objects().delete()
    Group.objects().delete()
    return jsonify({'message': 'Database has been flushed'})


@debug_pages.route('/test', methods=['GET', 'POST'])
@login_required
@admin_permission.require(http_exception=403)
def test():
    logging.getLogger().critical("critical message")
    logging.getLogger().warning("warning message")
    logging.getLogger().info("info message")
    logging.getLogger().debug("debug message")
    return ResponseBuilder().succeed(msg="it works").build()
    # return jsonify(dict(msg="it works"))


@debug_pages.route('/schemas', methods=['GET', 'POST'])
def schemas(**kwargs):
    schema =  BaseResponse()
    return schema.dump(dict(failed=False))
    # return ResponseBuilder().succeed(msg="it works").build()
    # return jsonify(dict(msg="it works"))


