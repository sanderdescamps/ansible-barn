from marshmallow import Schema, fields

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
    name = fields.Str()
    regex = fields.Bool(default=False)

class HostPutQueryArgsSchema(Schema):
    name = fields.Str()
    action = fields.Str(default="present", choices=["present","add","update","set"])
    vars = fields.Dict(description="Variables to add or update", example=dict(organisation_environment="development",creation_date="29-11-2020" ))
    groups = fields.List(fields.Str(), description="Alias for 'groups_present'", example=["example_group"])
    groups_present = fields.List(fields.Str(), description="Ensures that host belongs to the groups. Keeps the already assigned groups.", example=["example_group"])
    groups_absent = fields.List(fields.Str(), description="Removes host form groups", example=["leave_group"])
    groups_set = fields.List(fields.Str(), description="Host only belongs to the given groups. Mutually exclusive with groups, groups_present, groups_absent ", example=["example_group","all_servers"])
    create_groups = fields.Bool(default=True, description="When an unexisting group is configured it will be created.")
    vars_absent = fields.List(fields.Str(), description="Removes variables from host", example=["old_variable"])

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

