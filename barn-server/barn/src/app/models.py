import uuid
from mongoengine import StringField, BooleanField, DictField, ListField, ReferenceField
from werkzeug.security import generate_password_hash
from app import db


class Role(db.Document):
    name=StringField(required=True)
    description=StringField()

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return str(self.name)

    def __str__(self):
        return str(self.name)
    
    def __eq__(self,other):
        if other.__class__ == str:
            return (str(self.name).lower() == other.lower())
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
    roles= ListField(ReferenceField(Role))
    
    def __init__(self,*args, **kwargs):
        if "password" in kwargs and kwargs.get("password") is not None:
            kwargs["password_hash"] = generate_password_hash(kwargs.pop("password"), method='sha256')
        super(User, self).__init__(*args, **kwargs)   

    def __repr__(self):
        return '<User %r>' % (self.name)

    def has_role(self, role):
        return role in self.roles

    def roles_check(self,*roles):
        if self.admin or roles is None or "admin" in self.roles:
            return True
        
        for r in roles:
            if not self.has_role(r):
                return False
        return True

    def missing_roles(self,roles):
        missing_roles = []
        if self.admin or roles is None or "admin" in self.roles:
            return []
        for r in roles:
            if not self.has_role(r):
                missing_roles.append(r)
        return missing_roles


class Node(db.Document):
    name=StringField(required=True, unique=True)
    vars=DictField(default={})
    meta = {'allow_inheritance': True}

class Host(Node):
    groups=ListField(default=[])

class Group(Node):
    hosts=ListField(default=[])
    parent_groups=ListField(ReferenceField('Group'))
    child_groups=ListField(ReferenceField('Group'))

    def addChildGroupObject(self,o_groups):
        """
            Add list of groups as child groups

            Parameters:
            o_groups (list(Group)): list of child group objects

        """

        self.child_groups.extend(o_groups).save()
        for g in o_groups:
            g.parent_groups.append(self).save()

        
    def addparentGroupObject(self,o_groups):
        """
            Add list of groups as parent groups

            Parameters:
            o_groups (list(Group)): list of parent group objects

        """

        self.parent_groups.extend(o_groups).save()
        for g in o_groups:
            g.child_groups.append(self).save()
