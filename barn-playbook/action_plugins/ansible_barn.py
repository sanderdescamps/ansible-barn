from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.action import ActionBase
from ansible.module_utils.urls import Request
from datetime import datetime
import json

# from ansiblebarn.BarnBuilder import barnBuilder

token_cache={}

class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        module_args = self._task.args.copy()

        barn_host=module_args.get("host",None)
        barn_port=module_args.get("port",443)
        barn_user=module_args.get("user",None)
        barn_password=module_args.get("password",None)


        if barn_host in None:
           result['failed'] = True
           result['msg'] = "host is required"

        global token_cache
        token=None
        if bool(barn_user) and bool(barn_password):
            token_cache_index=hash([barn_user, barn_host, barn_password])
            token=token_cache.get(token_cache_index, None)

        host=task_vars.get("inventory_hostname")

        data={
            "name": host
        }

        r = Request().open("POST","http://%s:%s/query"%(barn_host,barn_port),
                               data=json.dumps(data).encode('utf-8'),
                               headers={'Content-type': 'application/json', "x-access-tokens": token})

        
        result["changed"] = changed
        return result