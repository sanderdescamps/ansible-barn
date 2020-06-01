import argparse
import configparser
import os.path
from ansible_barn.InventoryDB.MongoInventoryDB import MongoInventoryDB
import json
import yaml
from ansible_barn.BarnBuilder import barnBuilder

BARN_CONFIG_PATH=["~/.barn.cfg", "./barn.cfg", "/etc/ansible/barn.cfg"]

def main(command_line=None): 
    parser = argparse.ArgumentParser()
    barn_auth=parser.add_argument_group('barn authentication')
    barn_auth.add_argument("--barn_user",action="store", default=None)
    barn_auth.add_argument("--barn_password",action="store", default=None)
    barn_auth.add_argument("--barn_hostname",action="store", default=None)
    barn_auth.add_argument("--barn_port",action="store", default=None)
    barn_auth.add_argument("--barn_inventory_type",action="store",choices=('mongodb', 'elastic'), default=None, help='Barn database type (default: mongodb)')
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

    # ansible-barn push-variable
    show_parser = actionparsers.add_parser('show', help='Push a variable through all hosts in a group')
    show_parser.add_argument('name', action='store', default=None, nargs="?", help='Name of the group/host')
    show_parser.add_argument('--format','-f', action='store', default="json", help='Format of the output (json,yaml,text)')
    show_parser.add_argument('--json', action='store_true', default=False, help='output in json')
    show_parser.add_argument('--yaml','--yml', action='store_true', default=False, help='output in yaml')
    show_parser.add_argument('--text', action='store_true', default=False, help='output in json')

    args = parser.parse_args(command_line)
    
    v_args = vars(args)
    cli_prop = { k: v_args[k] for k in ["barn_user","barn_password","barn_hostname","barn_port", "barn_inventory_type"] if v_args[k] is not None }
    barnBuilder.config_manager.load_extra_vars(cli_prop)

    barn = barnBuilder.get_instance()

    
    
    if args.command == "add":
        if args.host_or_group == "host": 
            barn.add_host(args.name)
        else:
            barn.add_group(args.name)
    elif args.command == "set-variable" or args.command == "set-var":
        barn.set_variable(args.name, args.key, args.value)
    elif args.command == "show":
        if args.format.lower() == "text" or args.text == True:
            print(barn.export(args.name))
        elif args.format.lower() == "yaml"  or args.format.lower() == "yml" or args.yaml == True:
            print(yaml.dump(barn.export(args.name), sort_keys=True, indent=2))
        elif args.format.lower() == "json" or args.json == True:
            print(json.dumps(barn.export(args.name), sort_keys=True, indent=2))
    else: 
        print("command %s not supported"%(args.command))

if __name__ == '__main__':
    main()