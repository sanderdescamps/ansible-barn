import logging
import traceback
from flask import jsonify, make_response
from flask_login import current_user
from flask_principal import Permission

#400
def handle_bad_request(e):
    data = dict(
        msg=e.description if hasattr(e, 'description') else "Bad request",
        status=400,
    )
    return jsonify(data), 400

#401
def handle_authentication_failed(e):
    data = dict(
        msg=e.description if hasattr(e, 'description') else "Authentication failed",
        status=401
    )
    header = {"WWW-Authenticate": 'Basic realm="Login!"'}
    return make_response(jsonify(data), 401, header)

#403
def handle_forbidden(e):
    required_permission = getattr(e, "description", None)
    if isinstance(required_permission, Permission):
        needs = getattr(required_permission, "needs", [])
        msg = "Insufficient permissions. Action requires [{}] permissions".format(",".join([str(need.value) for need in needs]))
    else:
        msg = "Insufficient permissions"
    data = dict(
        msg=msg,
        status=403,
    )
    logging.getLogger().warning("Insufficient permissions: {} requires [{}] permissions".format(getattr(current_user,"username","Unknown user"),",".join([str(need.value) for need in needs])))
    header = {"WWW-Authenticate": 'Basic realm="Login!"'}
    return make_response(jsonify(data), 403, header)

#404
def handle_not_found(e):
    data = dict(
        msg=e.description if hasattr(e, 'description') else "Page not found",
        status=404,
    )
    return jsonify(data), 404

#500
def handle_internal_server_error(e):
    logging.getLogger().error("Internal server error\n%s",e)
    data = dict(
        msg=e.description if hasattr(e, 'description') else "Internal server error",
        status=500
    )
    return make_response(jsonify(data), 500)

# MongoDB error
def handle_mongodb_unreachable(_):
    logging.getLogger().error("MongoDB unreachable")
    data = dict(
        msg="Can't connect to MongoDB",
        status=500
    )
    return make_response(jsonify(data), 500)

#Catch them all
def pokemon_exception_handler(e):
    track = traceback.format_exc()
    logging.getLogger().error("Unknown Exception\n%s", track)
    data = dict(
        msg=str(e.description) if hasattr(e, 'description') else "Unknown Exception, check the logs for more details",
        status=e.code if hasattr(e, 'code') else 500,
    )
    return make_response(jsonify(data), 500)