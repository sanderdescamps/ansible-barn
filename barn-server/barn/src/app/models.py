import uuid
from abc import abstractmethod
from mongoengine import Document, StringField, DictField, ListField, ReferenceField
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

    @classmethod
    def from_json(cls, json_data, created=False, append=False):
        if json_data.get("type","").lower() == "host":
            return Host.from_json(json_data, created=created, append=append)
        elif json_data.get("type","").lower() == "group":
            return Group.from_json(json_data, created=created, append=append)
        else:
            raise ValueError

    def set_vars(self, vars_data):
        self.vars = vars_data

    def update_vars(self, vars_data):
        self.vars.update(vars_data)



class Host(Node):
    def get_hosts(self):
        return [self]

    def to_barn_dict(self):
        return dict(
            name=self.name,
            type="host",
            vars=self.vars
        )
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
            type="group",
            vars=self.vars,
            hosts=[host.name for host in self.hosts],
            child_groups=[group.name for group in self.child_groups]
        )

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
            if o_child_group: 
                self.child_groups.append(o_child_group)
        else:
            raise TypeError

    def add_child_groups(self, child_groups):
        for child_group in child_groups:
            self._add_child_group(child_group)

    def _set_host(self, host):
        if isinstance(host, Host):
            self.hosts.append(host)
        elif isinstance(host, str):
            o_host = Host.objects(name=host).first()
            if o_host:
                self.hosts.append(o_host)
        else:
            raise TypeError

    def set_hosts(self, hosts):
        for host in hosts:
            self._set_host(host)

    def _add_host(self, host):
        if isinstance(host, Host) and host not in self.hosts:
            self.hosts.append(host)
        elif isinstance(host, str):
            o_host = Host.objects(name=host).first()
            if o_host and host not in self.hosts:
                self.hosts.append(host)
        else:
            raise TypeError

    def add_hosts(self, hosts):
        for host in hosts:
            self._add_host(host)

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
