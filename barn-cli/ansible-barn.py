import argparse
import configparser
import os.path
from ansible_barn.InventoryDB.MongoInventoryDB import MongoInventoryDB


BARN_CONFIG_PATH=["~/.barn.cfg", "./barn.cfg", "/etc/ansible/barn.cfg"]
barn=None

def __read_cfg_files():
    res = {}
    for p in BARN_CONFIG_PATH:
        if os.path.isfile(p):
            config = configparser.ConfigParser()
            config.read(p)
            for k,v in config.items('defaults'):
                res[k] = v
    return res

def __read_env_vars():
    res = {}
    if "BARN_USER" in os.environ:
        res["barn_user"] = os.environ["BARN_USER"]
    if "BARN_PASSWORD" in os.environ:
        res["barn_password"] = os.environ["BARN_PASSWORD"]
    if "BARN_HOSTNAME" in os.environ:
        res["barn_hostname"] = os.environ["BARN_HOSTNAME"]
    return res

def load_properties():
    prop=__read_cfg_files()
    prop.update(__read_env_vars())
    return prop

def connect(prop):
    global barn
    barn=MongoInventoryDB(prop["barn_hostname"],port=prop["barn_port"],username=prop["barn_user"],password=prop["barn_password"])
    

def main(command_line=None): 
    parser = argparse.ArgumentParser()
    barn_auth=parser.add_argument_group('barn authentication')
    barn_auth.add_argument("--barn_user",action="store", default=None)
    barn_auth.add_argument("--barn_password",action="store", default=None)
    barn_auth.add_argument("--barn_hostname",action="store", default=None)
    barn_auth.add_argument("--barn_port",action="store", default=27017)

    actionparsers = parser.add_subparsers(help='commands',dest='command')

    # ansible-barn add 
    add_parser = actionparsers.add_parser('add', help='Add host or group to ansible-barn')
    add_parser.add_argument('host_or_group', action='store', choices=('host', 'group'), help='add host or group')
    add_parser.add_argument('name', action='store', help='Name of the host or group')
    add_parser.add_argument('--force-new','-f', action='store_true', help='Remove old host/group and add new one')

    # ansible-barn set-variable
    set_variable_parser = actionparsers.add_parser('set-variable', aliases=['set-var'], help='Assign variable to a host or a group')
    set_variable_parser.add_argument('name', action='store', help='Name of the host/group')
    set_variable_parser.add_argument('key', action='store', help='Variable name')
    set_variable_parser.add_argument('value', action='store',help='Variable value')

    # ansible-barn push-variable
    push_variable_parser = actionparsers.add_parser('push-variable', aliases=['push-var'], help='Push a variable through all hosts in a group')
    push_variable_parser.add_argument('name', action='store', help='Name of the group')
    push_variable_parser.add_argument('key', action='store', help='Variable name')
    push_variable_parser.add_argument('value', action='store',help='Variable value')

    args = parser.parse_args(command_line)
    
    prop = load_properties()
    v_args = vars(args)
    cli_prop = { k: v_args[k] for k in ["barn_user","barn_password","barn_hostname","barn_port"] if v_args[k] is not None }
    prop.update(cli_prop)
    connect(prop)

    
    
    if args.command == "add":
        if args.host_or_group == "host": 
            barn.add_host(args.name)
        else:
            barn.add_group(args.name)
    elif args.command == "set-variable":
        barn.set_variable(args.name, args.key, args.value)





if __name__ == '__main__':
    main()