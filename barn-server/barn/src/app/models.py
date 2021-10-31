import logging
import uuid
try:
    import ujson as json
except ImportError:
    import json
from abc import abstractmethod
from mongoengine import Document, StringField, DictField, ListField, ReferenceField, BooleanField
from werkzeug.security import generate_password_hash
from flask_login.mixins import UserMixin
from flask_principal import RoleNeed
from app.utils import remove_empty_fields



# class Role(Document):
#     name = StringField(required=True)
#     description = StringField()
#     # methode = StringField(required=True)

#     def __unicode__(self):
#         return self.name

#     def __repr__(self):
#         return str(self.name)

#     def __str__(self):
#         return str(self.name)

#     def __eq__(self, other):
#         if other.__class__ == str:
#             return str(self.name).lower() == other.lower()
#         else:
#             return (
#                 self.__class__ == other.__class__ and
#                 str(self.name).lower() == str(other.name).lower()
#             )

#     def to_tuple(self):
#         return RoleNeed(**{'value':self.name})


class User(Document, UserMixin):
    public_id = StringField(default=str(uuid.uuid4()))
    name = StringField()
    username = StringField(required=True, unique=True)
    password_hash = StringField()
    roles = ListField(default=[])
    active = BooleanField(default=True)

    def __init__(self, *args, **kwargs):
        if "password" in kwargs and kwargs.get("password") is not None:
            kwargs["password_hash"] = generate_password_hash(
                kwargs.pop("password"), method='sha256')
        # if "roles" in kwargs:
        #     roles = kwargs.pop("roles")
        #     o_roles = []
        #     if isinstance(roles, str):
        #         roles = roles.split(",")
            
        #     for role in roles:
        #         if isinstance(role, str):
        #             o_role = Role.objects(name=role).first()
        #             if o_role:
        #                 o_roles.append(o_role)
        #         elif isinstance(role, Role):
        #             o_roles.append(role)
        #     kwargs["roles"] = o_roles
        if kwargs.pop("admin", False):
            # o_admin = Role.objects(name__iexact="admin").first()
            # kwargs["roles"] = kwargs.get("roles",[]).append(o_admin)
            kwargs["roles"] = kwargs.get("roles", []) + ["admin"]
        super().__init__(*args, **kwargs)

    def to_barn_dict(self):
        return dict(
            name=self.name,
            username=self.username,
            public_id=self.public_id,
            type="user",
            active=self.active,
            roles=self.roles
        )

    def reset_password(self, password):
        self.password_hash = generate_password_hash(password, method='sha256')

    def __repr__(self):
        return '<User %r>' % (self.name)
    
    def get_id(self):
        return self.public_id

    def has_role(self, role):
        return role in self.roles

    def get_roles(self):
        return [RoleNeed(**{'value':role}) for role in self.roles]

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

    def __hash__(self):
        return hash((self.name, self.username, self.public_id, self.password_hash, self.active, frozenset(self.roles)))


class Node(Document):
    name = StringField(required=True, unique=True)
    vars = DictField(default={})
    meta = {'allow_inheritance': True}
    crates = ListField(ReferenceField('Crate'),default=[])


    @abstractmethod
    def get_hosts(self, recursive=False):
        return [self]

    @abstractmethod
    def to_barn_dict(self):
        pass

    @abstractmethod
    def format(self, empty_keys=True, parent_vars=False):
        pass

    @classmethod
    def from_json(cls, json_data, created=False, append=False):
        if json_data.get("type","").lower() == "host":
            return Host.from_json(json_data, created=created, append=append)
        elif json_data.get("type","").lower() == "group":
            return Group.from_json(json_data, created=created, append=append)
        else:
            raise ValueError

    def get_vars(self, parent_vars=False):
        if parent_vars:
            vars_copy = self.vars.copy()
            vars_copy.update(self.get_parent_vars())
            return vars_copy
        else:
            return self.vars

    @abstractmethod
    def get_parent_vars(self):
        return {}

    def set_vars(self, vars_data):
        self.vars = vars_data

    def update_vars(self, vars_data):
        self.vars.update(vars_data)

    def __str__(self):
        return self.name

    def subscribe_crate(self, crate):
        if crate not in self.crates:
            self.crates.append(crate)
            return True
        return False

    def unsubscribe_crate(self, crate):
        if crate in self.crates:
            self.crates.remove(crate)
            return True
        return False

    def get_crates(self):
        return list(self.crates)

class Host(Node):
    def get_hosts(self, recursive=False):
        return [self]

    def to_barn_dict(self, parent_vars=False):
        return dict(
            name=self.name,
            type="host",
            vars=self.get_vars(parent_vars=parent_vars)
        )

    def format(self, empty_values=True, parent_vars=False, **kwargs):
        """Return a directory of the host object. 
        Args:
            empty_values (bool): If False all null and empty values (or keys) will be removed frm the output. 
            parent_vars (bool): Add parent variables

        Returns:
            [dict]: dictionary output of the host object
        """
        output = dict(
            name=self.name,
            type="host",
            vars=self.get_vars(parent_vars=parent_vars)
        )
        if not empty_values:
            output["vars"] = remove_empty_fields(output["vars"])
        return output



    def get_parent_vars(self):
        parent_vars = {}
        o_parent_groups = Group.objects(hosts__in=[self])
        if not o_parent_groups:
            return {}
        for o_parent_group in o_parent_groups:
            parent_vars.update(o_parent_group.get_vars())
        return parent_vars
        

    @classmethod
    def from_json(cls, json_data, created=False, append=False):
        if json_data.get("name"):
            o_host = Host.objects(name=json_data.get("name")).first()
            if not o_host:
                o_host = Host(name=json_data.get("name"))
            if append:
                o_host.update_vars(json_data.get("vars",{}))
            else:
                o_host.set_vars(json_data.get("vars",{}))
            return o_host
        else:
            raise ValueError

class Group(Node):
    # hosts = ListField(default=[])
    hosts = ListField(ReferenceField('Host'), default=[])
    # parent_groups=ListField(ReferenceField('Group'))
    child_groups = ListField(ReferenceField('Group'), default=[])

    def get_hosts(self, recursive=False):
        """Return all hosts inside the group

        Args:
            recursive (bool, optional): Add all hosts of child-groups. Defaults to False.

        Returns:
            list: List of host objects
        """
        result = self.hosts
        if recursive:
            for child_group in self.child_groups:
                result.extend(child_group.get_hosts(recursive=recursive))
        return result

    def to_barn_dict(self, parent_vars=False):
        return dict(
            name=self.name,
            type="group",
            vars=self.get_vars(parent_vars=parent_vars),
            hosts=[host.name for host in self.hosts],
            child_groups=[group.name for group in self.child_groups]
        )
    
    def format(self, empty_values=True, parent_vars=False, **kwargs):
        """Return a directory of the host object. 
        Args:
            empty_values (bool): If False all null and empty values (or keys) will be removed frm the output. 
            parent_vars (bool): Add parent variables

        Returns:
            [dict]: dictionary output of the host object
        """
        output = dict(
            name=self.name,
            type="host",
            vars=self.get_vars(parent_vars=parent_vars)
        )
        if not empty_values:
            output["vars"] = remove_empty_fields(output["vars"])
        return output


    def get_parent_vars(self):
        parent_vars = {}
        o_parent_groups = Group.objects(child_groups__in=[self])
        if not o_parent_groups:
            return {}
        for o_parent_group in o_parent_groups:
            parent_vars.update(o_parent_group.get_vars())
        return parent_vars

    def set_child_groups(self,child_groups):
        for child_group in child_groups:
            self._set_child_group(child_group)
            
    def _set_child_group(self, child_group):
        if isinstance(child_group, Group):
            self.child_groups = [child_group]
        elif isinstance(child_group, str):
            o_child_group = Group.objects(name=child_group).first()
            if o_child_group: 
                self.child_groups = [o_child_group]
        else:
            raise TypeError

    def _add_child_group(self, child_group):
        if isinstance(child_group, Group) and child_group not in self.child_groups:
            self.child_groups.append(child_group)
        elif isinstance(child_group, str):
            o_child_group = Group.objects(name=child_group).first()
            if o_child_group and o_child_group not in self.child_groups: 
                self.child_groups.append(o_child_group)
        else:
            raise TypeError

    def add_child_groups(self, child_groups):
        for child_group in child_groups:
            self._add_child_group(child_group)

    def set_hosts(self, hosts):
        """Set list of hosts"""
        self.hosts = []
        self.add_hosts(hosts)

    def _add_host(self, host):
        if isinstance(host, Host) and host not in self.hosts:
            self.hosts.append(host)
        elif isinstance(host, str):
            o_host = Host.objects(name=host).first()
            if o_host and o_host not in self.hosts:
                self.hosts.append(o_host)
        else:
            raise TypeError

    def add_hosts(self, hosts):
        """Add list of hosts to the current hosts"""
        if type(hosts) is Host:
            hosts = [hosts]
        for host in hosts:
            self._add_host(host)

    def __str__(self):
        return str(self.name)

    @classmethod
    def from_json(cls, json_data, created=False, append=False):
        if json_data.get("name"):
            o_group = Group.objects(name=json_data.get("name")).first()
            if not o_group:
                o_group = Group(name=json_data.get("name"))
            if append:
                o_group.update_vars(json_data.get("vars",{}))
                o_group.add_child_groups(json_data.get("child_groups",[]))
                o_group.add_hosts(json_data.get("hosts",[]))
            else:
                o_group.set_vars(json_data.get("vars",{}))
                o_group.set_child_groups(json_data.get("child_groups",[]))
                o_group.set_hosts(json_data.get("hosts",[]))
            return o_group
        else:
            raise ValueError



class Crate(Document):

    crate_id=StringField(unique=True, required=True)
    type=StringField(required=True)
    vars = DictField(default={})

    def __init__(self, *args, **values):
        values["crate_id"] = values.get("crate_id") or str(uuid.uuid4())
        super().__init__(*args, **values)
    
    def __hash__(self):
        return hash(json.dumps(dict(
            crate_id=self.crate_id,
            type=self.type,
            vars=self.vars
            )))

    def to_barn_dict(self, parent_vars=False):
        return dict(
            type=self.type,
            vars=self.vars,
            crate_id=self.get_id(),
            assigned_to=[n.name for n in self.get_subscribers()],
        )

    def get_id(self):
        return self.crate_id

    def get_subscribers(self, recursive=False):
        o_subscribers = list(Node.objects(crates__in=[self]))
        if not recursive:
            return o_subscribers
        
        o_subsc_hosts = set()
        for n in o_subscribers:
            o_subsc_hosts.update(n.get_hosts(recursive=recursive))
        return list(o_subsc_hosts)

    def __str__(self):
        return "%s_%s"%("Crate", str(self.get_id()))

        
