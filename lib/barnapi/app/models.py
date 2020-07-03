import uuid
from mongoengine import StringField, BooleanField, IntField, DictField, ListField, UUIDField, ReferenceField
from werkzeug.security import generate_password_hash
from app import db
from app.app_utils import deprecated

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

    def to_dict(self, hide_id=False, ref_resolve=False, use_db_field=True):
        som = self.to_mongo(use_db_field)
        som.pop('_id')
        return som.to_dict()


class Host(Node):
    groups=ListField(default=[])

class Group(Node):
    hosts=ListField(default=[])
    parent_groups=ListField(ReferenceField('Group'))
    child_groups=ListField(ReferenceField('Group'))

    @deprecated
    def addChildGroup(self,group_name):
        """
            Add a group as a child group

            Parameters:
            group_name (string): name of the group

            Returns:
            bool:returns True if group is added to group
        """
        o_childgroup = Group.objects(name=group_name).first()
        if o_childgroup is not None:
            self.child_groups.append(o_childgroup).save()
            o_childgroup.parent_groups.append(self).save()
            return True
        else:
            return False

    def addChildGroupObject(self,o_groups):
        """
            Add list of groups as child groups

            Parameters:
            o_groups (list(Group)): list of child group objects

        """

        self.child_groups.extend(o_groups).save()
        for g in o_groups:
            g.parent_groups.append(self).save()


    @deprecated
    def addParentGroup(self,group_name):
        """
            Add a group as a parent group

            Parameters:
            group_name (string): name of the group

            Returns:
            bool:returns True if group is added to group
        """
        o_parentgroup = Group.objects(name=group_name).first()
        if o_parentgroup is not None:
            self.parent_groups.append(o_parentgroup).save()
            o_parentgroup.child_groups.append(self).save()
            return True
        else:
            return False
        
    def addparentGroupObject(self,o_groups):
        """
            Add list of groups as parent groups

            Parameters:
            o_groups (list(Group)): list of parent group objects

        """

        self.parent_groups.extend(o_groups).save()
        for g in o_groups:
            g.child_groups.append(self).save()
