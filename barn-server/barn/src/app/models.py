import uuid
from abc import abstractmethod
from mongoengine import Document, StringField, BooleanField, DictField, ListField, ReferenceField
from werkzeug.security import generate_password_hash


class Role(Document):
    name = StringField(required=True)
    description = StringField()

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return str(self.name)

    def __str__(self):
        return str(self.name)

    def __eq__(self, other):
        if other.__class__ == str:
            return str(self.name).lower() == other.lower()
        else:
            return (
                self.__class__ == other.__class__ and
                str(self.name).lower() == str(other.name).lower()
            )


class User(Document):
    public_id = StringField(default=str(uuid.uuid4()))
    name = StringField()
    username = StringField(required=True, unique=True)
    password_hash = StringField()
    roles = ListField(ReferenceField(Role))

    def __init__(self, *args, **kwargs):
        if "password" in kwargs and kwargs.get("password") is not None:
            kwargs["password_hash"] = generate_password_hash(
                kwargs.pop("password"), method='sha256')
        if "roles" in kwargs:
            roles = kwargs.pop("roles")
            o_roles = []
            if isinstance(roles, str):
                roles = roles.split(",")
            for role in roles:
                if isinstance(role, str):
                    o_role = Role.objects(name=role).first()
                    if o_role:
                        o_roles.append(o_role)
                elif isinstance(role, Role):
                    o_roles.append(role)
            kwargs["roles"] = o_roles
        if kwargs.pop("admin", False):
            o_admin = Role.objects(name__iexact="admin").first()
            kwargs["roles"] = kwargs.get("roles",[]).append(o_admin)
        super(User, self).__init__(*args, **kwargs)

    def __repr__(self):
        return '<User %r>' % (self.name)

    def has_role(self, role):
        return role in self.roles

    def isadmin(self):
        if self.roles is not None and "admin" in self.roles:
            return True
        return False

    def missing_roles(self, roles):
        missing_roles = []

        if self.isadmin():
            return []
        for role in roles:
            if not self.has_role(role):
                missing_roles.append(role)
        return missing_roles


class Node(Document):
    name = StringField(required=True, unique=True)
    vars = DictField(default={})
    meta = {'allow_inheritance': True}

    @abstractmethod
    def get_hosts(self):
        return

    @abstractmethod
    def to_barn_dict(self):
        pass


class Host(Node):
    def get_hosts(self):
        return [self]

    def to_barn_dict(self):
        return dict(
            name=self.name,
            cls="host",
            vars=self.vars
        )

class Group(Node):
    # hosts = ListField(default=[])
    hosts = ListField(ReferenceField('Host'))
    # parent_groups=ListField(ReferenceField('Group'))
    child_groups = ListField(ReferenceField('Group'))

    def get_hosts(self):
        result = self.hosts
        for child_group in self.child_groups:
            result.extend(child_group.get_hosts())
        return result

    def to_barn_dict(self):
        return dict(
            name=self.name,
            cls="group",
            vars=self.vars,
            hosts=[host.name for host in self.hosts],
            child_groups=[group.name for group in self.child_groups]
        )