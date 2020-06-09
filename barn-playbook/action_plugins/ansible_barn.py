from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.action import ActionBase
from datetime import datetime
from ansiblebarn.BarnBuilder import barnBuilder

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)
        module_args = self._task.args.copy()

        barn_config={}
        if "host" in module_args and module_args["host"] is not None:
            barn_config["barn_hostname"] = module_args["host"]
        if "port" in module_args and module_args["port"] is not None:
            barn_config["barn_port"] = module_args["port"]
        if "user" in module_args and module_args["user"] is not None:
            barn_config["barn_user"] = module_args["user"]
        if "password" in module_args and module_args["password"] is not None:
            barn_config["barn_password"] = module_args["password"]
        if "barn_type" in module_args and module_args["barn_type"] is not None:
            barn_config["barn_inventory_type"] = module_args["barn_type"]

        barnBuilder.config_manager.load_extra_vars(barn_config)
        barn = barnBuilder.get_instance()
        inv_host=task_vars["inventory_hostname"]


        if "data" in module_args and isinstance(module_args["data"],dict):
            data = module_args["data"] 
            current_vars=barn.get_vars(inv_host)
            print(current_vars)
            changed = False

            if "state" in module_args and module_args["state"] == "present":
                for k,v in data.items():
                    print("key:%s value:%s"%(k,v))
                    if barn.host_exist(inv_host) and not (k in current_vars and (current_vars[k] == v)):
                        print(changed)
                        barn.set_variable(inv_host,k,v)
                        changed = True
            elif "state" in module_args and module_args["state"] == "absent":
                for k in data.keys():
                    if k in current_vars:
                        barn.delete_variable(inv_host,k)
                        changed=True
            elif "state" in module_args and module_args["state"] == "show":
                result["output"] = barn.get_vars(inv_host)
        result["changed"] = changed
        return result