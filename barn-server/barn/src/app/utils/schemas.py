from marshmallow import Schema, fields, pre_load, validate
from marshmallow.utils import pprint
from flask_smorest.fields import Upload
from app.utils import boolean_parser, list_parser

class CrateSchema(Schema):
    id=fields.Str()
    type=fields.Str()
    vars = fields.Dict(Default={})

class NodeSchema(Schema):
    name = fields.Str(description='Name of the Node')
    vars = fields.Dict(Default={})
    type= fields.Str(default="node")
    crates = fields.List(fields.Nested(CrateSchema))

class GroupSchema(NodeSchema):
    name = fields.Str(example='dns_servers')
    hosts = fields.List(fields.Str)
    type= fields.Str(default="group")
    child_groups = fields.List(fields.Str)

class HostSchema(NodeSchema):
    type= "host"

class HostQueryArgsSchema(Schema):
    name = fields.Str(description="Name of the host (wildcard: '*')")
    regex = fields.Bool(description="When true name will be rocessed as regular expression", default=False)

class HostPutQueryArgsSchema(Schema):
    name = fields.Str()
    action = fields.Str(default="present", choices=["present","add","update","set"])
    vars = fields.Dict(description="Variables to add or update", example=dict(organisation_environment="development",creation_date="29-11-2020" ))
    groups = fields.List(fields.Str(), description="Alias for 'groups_present'", example=["example_group"], list_parser=True)
    groups_present = fields.List(fields.Str(), description="Ensures that host belongs to the groups. Keeps the already assigned groups.", example=["example_group"], list_parser=True, aliases=["groups"])
    groups_absent = fields.List(fields.Str(), description="Removes host form groups", example=["leave_group"], list_parser=True)
    groups_set = fields.List(fields.Str(), description="Host only belongs to the given groups. Mutually exclusive with groups_present and groups_absent ", example=["example_group","all_servers"], list_parser=True)
    create_groups = fields.Bool(default=True, description="When an unexisting group is configured it will be created.")
    vars_absent = fields.List(fields.Str(), description="Removes variables from host", example=["old_variable"])

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
    name = fields.Str(description="Name of the group (wildcard: '*')")
    regex = fields.Bool(description="When true name will be rocessed as regular expression", default=False)
    
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
    
    create_groups = fields.Bool(default=True, description="When an unexisting group is configured it will be created.")
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
    def string2bool(self, data, **kwargs):
        for f,v in getattr(self,"fields",{}).items():
            if isinstance(v,fields.List) and v.metadata.get("boolean_parser",False):
                if f in data:
                    data[f] = boolean_parser(data.get(f))
        return data

class UploadQueryArgsSchema(Schema):
    files = fields.List(Upload())
    keep = fields.Boolean(default=False, description="Keep existing barn data", boolean_parser=True)
    
    @pre_load
    def string2bool(self, data, **kwargs):
        for f,v in getattr(self,"fields",{}).items():
            if isinstance(v,fields.List) and v.metadata.get("boolean_parser",False):
                if f in data:
                    data[f] = boolean_parser(data.get(f))
        return data

class BaseResponse(Schema):
    status = fields.Int(default=200, description='http status code', example=200)
    changed = fields.Bool(default=False, description='True if a change is made in the barn database.', example=False)
    failed = fields.Bool(default=False, description='True if operation failed', example=False)
    msg = fields.Str(description='The main message', example="This is a sample message")
    msg_list = fields.List(fields.Str, description='List of log messages', example=["This is a sample message"])

class BarnError(BaseResponse):
    errors = fields.Dict(metadata={"description": "'Details about the error'"})
    changed = fields.Bool(default=False, description='True if a change is made in the barn database.', example=False)
    failed = fields.Bool(default=False, description='True if operation failed', example=True)

class NodeResponse(BaseResponse):
    result = fields.List(fields.Nested(NodeSchema), description='Result with list of Nodes')

