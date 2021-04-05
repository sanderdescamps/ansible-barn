import logging
import re
from marshmallow import Schema, fields, pre_load, validate
from marshmallow.exceptions import ValidationError
from marshmallow.utils import pprint
from flask_smorest.fields import Upload
from app.utils import boolean_parser, list_parser

class CrateSchema(Schema):
    id=fields.String()
    type=fields.String()
    vars = fields.Dict(Default={})

class NodeSchema(Schema):
    name = fields.String(description='Name of the Node')
    vars = fields.Dict(Default={})
    type= fields.String(default="node")
    crates = fields.List(fields.Nested(CrateSchema))

class GroupSchema(NodeSchema):
    name = fields.String(example='dns_servers')
    hosts = fields.List(fields.String)
    type= fields.String(default="group")
    child_groups = fields.List(fields.String)

class HostSchema(NodeSchema):
    type=fields.String(default="host", validate=validate.OneOf("host"))

class NodeQueryArgsSchema(Schema):
    type = fields.String(description="Type of node", required=False, validate=validate.OneOf(["host","group"]))
    name = fields.String(description="Name of the host (wildcard: '*')")
    regex = fields.Boolean(description="When true name will be processed as regular expression", default=False)

class HostQueryArgsSchema(Schema):
    name = fields.String(description="Name of the host (wildcard: '*')")
    regex = fields.Boolean(description="When true name will be processed as regular expression", default=False)

class HostPutQueryArgsSchema(Schema):
    name = fields.String()
    action = fields.String(default="present", choices=["present","add","update","set"])
    vars = fields.Dict(description="Variables to add or update", example=dict(organisation_environment="development",creation_date="29-11-2020" ))
    groups = fields.List(fields.String(), description="Alias for 'groups_present'", example=["example_group"], list_parser=True)
    groups_present = fields.List(fields.String(), description="Ensures that host belongs to the groups. Keeps the already assigned groups.", example=["example_group"], list_parser=True, aliases=["groups"])
    groups_absent = fields.List(fields.String(), description="Removes host form groups", example=["leave_group"], list_parser=True)
    groups_set = fields.List(fields.String(), description="Host only belongs to the given groups. Mutually exclusive with groups_present and groups_absent ", example=["example_group","all_servers"], list_parser=True)
    create_groups = fields.Boolean(default=True, description="When an unexisting group is configured it will be created.")
    vars_absent = fields.List(fields.String(), description="Removes variables from host", example=["old_variable"])

    @pre_load
    def string2list(self, data, **kwargs):
        for f,v in getattr(self,"fields",{}).items():
            if isinstance(v,fields.List) and v.metadata.get("list_parser",False):
                if f in data:
                    data[f] = list_parser(data.get(f))
        return data

    @pre_load
    def field_aliasses(self, data, **kwargs):
        data = dict(data)
        for f,v in getattr(self,"fields",{}).items():
            if isinstance(v,fields.List) and v.metadata.get("aliases",False):
                for alias in list_parser(v.metadata.get("aliases",[])):
                    if f not in data and alias in data:
                        data[f] = data.pop(alias, None)
        return data


class GroupQueryArgsSchema(Schema):
    name = fields.String(description="Name of the group (wildcard: '*')")
    regex = fields.Boolean(description="When true name will be rocessed as regular expression", default=False)
    
class GroupPutQueryArgsSchema(Schema):
    name = fields.Str(description="Name of the group", example="staging_servers")
    child_groups = fields.List(fields.Str(), description="Alias for 'child_groups'", example=["staging_dns_servers"], list_parser=True)
    child_groups_present = fields.List(fields.Str(), description="Add one or more child groups.", example=["staging_dns_servers"], list_parser=True, aliases=["child_groups"])
    child_groups_absent = fields.List(fields.Str(), description="Remove one or more child groups.", example=["abandon_servers"], list_parser=True)
    child_groups_set = fields.List(fields.Str(), description="Set fixed list of childgroups. Remove all others. Mutually exclusive with child_groups_present and child_groups_absent ", example=["staging_amq_group","staging_dns_servers"], list_parser=True)
    
    parent_groups = fields.List(fields.Str(), description="Alias for 'parent_groups_present'", example=["all_servers"], list_parser=True)
    parent_groups_present = fields.List(fields.Str(), description="Add parent group if not already added", example=["all_servers"], list_parser=True, aliases=["parent_groups"])
    parent_groups_absent = fields.List(fields.Str(), description="Removes parent group", example=["leave_group"], list_parser=True)
    parent_groups_set = fields.List(fields.Str(), description="Set fixed list of parent groups. Remove all others. Mutually exclusive with parent_groups_present and parent_groups_absent ", example=["example_group","all_servers"], list_parser=True)
    
    create_groups = fields.Boolean(default=True, description="When an unexisting group is configured it will be created.")
    vars = fields.Dict(description="Variables to add or update", example=dict(environment="staging"))
    vars_absent = fields.List(fields.Str(), description="Removes variables from host", example=["old_variable"], list_parser=True)
    
    hosts = fields.List(fields.Str(), description="Alias for 'hosts_present'", example=["srvdns01"], list_parser=True)
    hosts_present = fields.List(fields.Str(), description="Add host to group", example=["srvdns01"], list_parser=True, aliases=["hosts"])
    hosts_absent = fields.List(fields.Str(), description="Remove host from group", example=["old_host"], list_parser=True)
    hosts_set = fields.List(fields.Str(), description="Set fixed list of hosts in the group. Remove all others. Mutually exclusive with hosts_present and hosts_absent ", example=["srvdns01","srvdns02"], list_parser=True)

    @pre_load
    def string2list(self, data, **kwargs):
        for f,v in getattr(self,"fields",{}).items():
            if isinstance(v,fields.List) and v.metadata.get("list_parser",False):
                if f in data:
                    data[f] = list_parser(data.get(f))
        return data

    @pre_load
    def field_aliasses(self, data, **kwargs):
        data = dict(data)
        for f,v in getattr(self,"fields",{}).items():
            if isinstance(v,fields.List) and v.metadata.get("aliases",False):
                for alias in list_parser(v.metadata.get("aliases",[])):
                    if f not in data and alias in data:
                        data[f] = data.pop(alias, None)
        return data

class ExportQueryArgsSchema(Schema):
    full = fields.Boolean(default=True, description="Keep empty fields", boolean_parser=True)
    format = fields.String(default="json", description="Format of the export", validate=validate.OneOf(["yaml","yml","json"]))
    file = fields.Boolean(default=False, description="Download export as file", boolean_parser=True)

    @pre_load
    def string2Boolean(self, data, **kwargs):
        for f,v in getattr(self,"fields",{}).items():
            if isinstance(v,fields.List) and v.metadata.get("boolean_parser",False):
                if f in data:
                    data[f] = boolean_parser(data.get(f))
        return data

class UploadQueryArgsSchema(Schema):
    files = fields.List(Upload())
    keep = fields.Boolean(default=False, description="Keep existing barn data", boolean_parser=True)
    
    @pre_load
    def string2Boolean(self, data, **kwargs):
        for f,v in getattr(self,"fields",{}).items():
            if isinstance(v,fields.List) and v.metadata.get("boolean_parser",False):
                if f in data:
                    data[f] = boolean_parser(data.get(f))
        return data

class RegisterUserArgsSchema(Schema):
    name=fields.String(description="Name of the user contains")
    username=fields.String(description="Username of the user.", required=True)
    password=fields.String(description="Password to authenticate")
    hashed_password=fields.String(description="SHA256 hash of the users password", validate=validate.Regexp(re.compile(r"^\$[5-6]\$.+$")))
    admin=fields.Boolean(description="True if user is admin user")


class UserQueryArgsSchema(Schema):
    name = fields.String(description="Name of the user")
    username=fields.String(description="Username of the user.")
    active=fields.Boolean(description="Is the user active", boolean_parser=True)
    public_id=fields.String(description="Public ID of the user object")
    
    @pre_load
    def string2Boolean(self, data, **kwargs):
        for f,v in getattr(self,"fields",{}).items():
            if isinstance(v,fields.List) and v.metadata.get("boolean_parser",False):
                if f in data:
                    data[f] = boolean_parser(data.get(f))
        return data

class UserPutQueryArgsSchema(Schema):
    username=fields.String(description="Username of the user.", required=True)
    name=fields.String(description="Name of the user contains")
    action=fields.String(description="Action of the request", validate=validate.OneOf(["add","update","present","passwd"]))
    password=fields.String(description="Password to authenticate")
    # password_hash=fields.Method("password_hash_parser","password_hash_parser", description=)
    password_hash=fields.String(description="""
    use:
        python -c 'from werkzeug.security import generate_password_hash; print(generate_password_hash("password", method="sha256"))'
    """, validate=validate.Regexp(r"sha(256|512)\$([^\$]+)\$([^\$]+)$"))
    active=fields.Boolean(description="Is the user active", boolean_parser=True)
    roles=fields.List(fields.String, description="List of roles", list_parser=True)
    admin=fields.Boolean(description="True if user is admin user")

    # def password_hash_parser(self,obj):
    #     logging.info(obj)
    #     if not isinstance(obj,str):
    #         raise ValidationError("'password_hash' need to be a string")
        
    #     password_hash = str(obj)
    #     match_sha_short = re.search(r"^\$([5-6])\$([^\$]+)\$([^\$]+)$", password_hash)
    #     if match_sha_short:
    #         if match_sha_short.group(1) == "5":
    #             return "sha256${}${}".format(match_sha_short.group(2), match_sha_short.group(3).encode("utf-8").hex())
    #         elif match_sha_short.group(1) == "6":
    #             return "sha512${}${}".format(match_sha_short.group(2), match_sha_short.group(3).encode("utf-8").hex())
    #     elif password_hash.startswith("sha256") or password_hash.startswith("sha512"):
    #         return password_hash
    #     else:
    #         raise ValidationError("""Incorrect password hash. Use: python -c 'from werkzeug.security import generate_password_hash; print(generate_password_hash("password", method="sha256"))' """) 
    #     return obj
    
    @pre_load
    def string2Boolean(self, data, **kwargs):
        for f,v in getattr(self,"fields",{}).items():
            if isinstance(v,fields.List) and v.metadata.get("boolean_parser",False):
                if f in data:
                    data[f] = boolean_parser(data.get(f))
        return data

    @pre_load
    def string2list(self, data, **kwargs):
        for f,v in getattr(self,"fields",{}).items():
            if isinstance(v,fields.List) and v.metadata.get("list_parser",False):
                if f in data:
                    data[f] = list_parser(data.get(f))
        return data

class BaseResponse(Schema):
    status = fields.Integer(default=200, description='http status code', example=200)
    changed = fields.Boolean(default=False, description='True if a change is made in the barn database.', example=False)
    failed = fields.Boolean(default=False, description='True if operation failed', example=False)
    msg = fields.String(description='The main message', example="This is a sample message")
    msg_list = fields.List(fields.Str, description='List of log messages', example=["This is a sample message"])

class BarnError(BaseResponse):
    errors = fields.Dict(metadata={"description": "'Details about the error'"})
    changed = fields.Boolean(default=False, description='True if a change is made in the barn database.', example=False)
    failed = fields.Boolean(default=False, description='True if operation failed', example=True)

class NodeResponse(BaseResponse):
    result = fields.List(fields.Nested(NodeSchema), description='Result with list of Nodes')


