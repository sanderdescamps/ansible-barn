import json
from ansible.plugins.action import ActionBase
from ansible.module_utils.urls import Request

class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):

        changed = False

        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        del tmp  # tmp no longer has any effect

        module_args = self._task.args.copy()

        barn_host = module_args.get("host", None)
        barn_port = module_args.get("port", 443)
        barn_user = module_args.get("user", None)
        barn_password = module_args.get("password", None)
        token = module_args.get("token", None)

        if barn_host is None:
            result['changed'] = False
            result['failed'] = True
            result['msg'] = "host is required"
            return result

        try:
            data={
                "name": task_vars.get("inventory_hostname"),
                'type': "host"
            }

            query_args = dict(data=json.dumps(data).encode('utf-8'))
            if token:
                query_args["headers"] = dict({
                    'Content-type': 'application/json',
                    "x-access-tokens": token
                })
            elif barn_user and barn_password:
                query_args["url_username"] = barn_user
                query_args["url_password"] = barn_password
                query_args["force_basic_auth"] = True
                query_args["headers"] = dict({
                    'Content-type': 'application/json'
                })
            r = Request().open("GET", "http://%s:%s/nodes"% (barn_host, barn_port), **query_args)
            
            result["vars"]=json.loads(r.read()).get("results",{})[0].get("vars",{})
        except FileExistsError as e:
            result['msg'] = e

        result["changed"] = changed
        return result
