from app import app
from app.models import User, Role, Host, Group
from mongoengine import EmbeddedDocumentField

Role.objects().delete()
r_admin=Role(name="Admin", description="Allow anything")
r_admin.save()
Role(name="AddHost", description="Add a host to the inventory").save()
Role(name="AddGroup", description="Add a group to the inventory").save()
Role(name="ReadOnly", description="Read access on inventory").save()

User.objects().delete()
u1 = User(name="Sander Descamps", username="sdescamps", password="testpassword")
u1.roles.append(r_admin)
u1.save()

Host.objects().delete()
Host(name="srvplex01.myhomecloud.be").save()
Host(name="srvdns01.myhomecloud.be").save()
Host(name="srvdns02.myhomecloud.be").save()

Group.objects().delete()
Group(name="dns_servers").save()
Group(name="all_servers").save()
