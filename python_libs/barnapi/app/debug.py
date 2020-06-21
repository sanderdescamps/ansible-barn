from app.models import User, Role, Host, Group

def db_init():
    Role.objects().delete()
    r_admin=Role(name="Admin", description="Allow anything")
    r_admin.save()
    Role(name="AddHost", description="Add a host to the inventory").save()
    Role(name="AddGroup", description="Add a group to the inventory").save()
    Role(name="ReadOnly", description="Read access on inventory").save()
    Role(name="Query", description="Read access on inventory").save()

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

def db_flush():
    # Role.objects().delete()
    # User.objects().delete()
    Host.objects().delete()
    Group.objects().delete()


if __name__ == "__main__":
    db_init()
