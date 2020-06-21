import uuid
from mongoengine import StringField, BooleanField, IntField, DictField, ListField, UUIDField, ReferenceField
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

class Author(db.Document):
    name = IntField(required=True, unique=True)
    country = StringField(required=True)
    user_id = IntField(required=True)

class Host(db.Document):
    name=StringField(required=True)
    vars=DictField(default={})
    groups=ListField(default=[])

class Group(db.Document):
    name=StringField(required=True)
    vars=DictField(default={})
    hosts=ListField(default=[])
    parent_groups=ListField(ReferenceField('Group'))
    child_groups=ListField(ReferenceField('Group'))

