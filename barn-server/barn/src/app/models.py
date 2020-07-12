import uuid
from abc import abstractmethod
from mongoengine import StringField, BooleanField, DictField, ListField, ReferenceField
from werkzeug.security import generate_password_hash
from app import db


class Role(db.Document):
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


class User(db.Document):
    public_id = StringField(default=str(uuid.uuid4()))
    name = StringField()
    username = StringField(required=True, unique=True)
    password_hash = StringField()
    admin = BooleanField(default=False)
    roles = ListField(ReferenceField(Role))

    def __init__(self, *args, **kwargs):
        if "password" in kwargs and kwargs.get("password") is not None:
            kwargs["password_hash"] = generate_password_hash(
                kwargs.pop("password"), method='sha256')
        super(User, self).__init__(*args, **kwargs)

    def __repr__(self):
        return '<User %r>' % (self.name)

    def has_role(self, role):
        return role in self.roles

    def missing_roles(self, roles):
        missing_roles = []

        if self.admin or roles is None or (self.roles is not None and "admin" in self.roles):
            return []
        for role in roles:
            if not self.has_role(role):
                missing_roles.append(role)
        return missing_roles


class Node(db.Document):
    name = StringField(required=True, unique=True)
    vars = DictField(default={})
    meta = {'allow_inheritance': True}

    @abstractmethod
    def get_hosts(self):
        return


class Host(Node):
    def get_hosts(self):
        return [self]


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
