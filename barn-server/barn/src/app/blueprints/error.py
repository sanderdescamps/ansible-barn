from flask import jsonify, make_response

#400
def handle_bad_request(e):
    data = dict(
        msg="Bad request",
        status=400,
    )
    return jsonify(data), 400

#401
def handle_authentication_failed(e):
    data = dict(
        msg=e.description if e.description else "Authentication failed",
        status=401,
        exeption=vars(e)
    )
    header = {"WWW-Authenticate": 'Basic realm="Login!"'}
    return make_response(jsonify(data), 401, header)