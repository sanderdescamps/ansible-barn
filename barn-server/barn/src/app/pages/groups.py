from flask import Blueprint, request, jsonify, make_response
from mongoengine.errors import NotUniqueError
from app.utils import list_parser, merge_args_data
from app.auth import authenticate
from app.models import Group

group_pages = Blueprint('group', __name__)


@group_pages.route('/groups', methods=['GET'])
@authenticate('getGroup')
def get_groups(current_user=None):
    args = merge_args_data(request.args, request.get_json(silent=True))

    query_args = dict()
    query_args["name"] = args.get("name", None)
    if not query_args["name"]:
        return jsonify(error='name not defined'), 400

    o_groups = Group.objects(**query_args)
    return jsonify({
        'results': o_groups,
        'failed': False,
        'msg': "return list of group(s)"
    })


@group_pages.route('/groups', methods=['PUT'])
@authenticate('getGroup')
def put_groups(current_user=None):
    args = merge_args_data(request.args, request.get_json(silent=True))

    query_args = dict()
    if "name" in args:
        query_args["name"] = args.get("name")
    else:
        return make_response('name not defined', 400)

    try:
        if "child_groups" in args:
            child_groups = list_parser(args.get("child_groups"))
            o_child_groups = Group.objects(name__in=child_groups)
            query_args["child_groups"] = o_child_groups
        o_group = Group(**query_args)
        o_group.save()

        if "parent_groups" in args:
            parent_groups = list_parser(args.get("parent_groups"))
            o_parent_groups = Group.objects(name__in=parent_groups)
            for o_parent_group in o_parent_groups:
                o_parent_group.update(add_to_set__child_groups=o_group)
    except NotUniqueError:
        return make_response('Duplicate Group: %s already exist' % (args.get("name")), 400)

    return jsonify({'message': 'Group Added'})


@group_pages.route('/groups', methods=['DELETE'])
@authenticate('deleteGroups')
def delete_groups(current_user=None):
    query_args = dict()
    if "name" in request.args:
        query_args["name__in"] = request.args.get("name").split(',')
    else:
        return jsonify(error='name not defined'), 400

    o_groups = Group.objects(**query_args)
    if o_groups.count() < 1:
        return jsonify(error='%s not found' % (request.args.get('name'))), 400
    s_groups = ','.join(o_groups.scalar('name'))
    o_groups.delete()
    return jsonify({'message': '%s have been deleted' % (s_groups)})
