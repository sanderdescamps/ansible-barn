from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.action import ActionBase
from ansible.module_utils.urls import Request
from ansible.module_utils.six import PY3
from datetime import datetime
import json

# from ansiblebarn.BarnBuilder import barnBuilder

print("Initiate TOKEN_CACHE")
TOKEN_CACHE = {}


class ActionModule(ActionBase):

    def _set_token_in_cache(self, barn_host, barn_port, barn_user, barn_password, token):
        token_cache_index = str(
            hash((barn_host, barn_port, barn_user, barn_password)))
        global TOKEN_CACHE
        TOKEN_CACHE[token_cache_index] = token

    def _get_token_from_cache(self, barn_host, barn_port, barn_user, barn_password):
        token_cache_index = str(
            hash((barn_host, barn_port, barn_user, barn_password)))
        global TOKEN_CACHE
        return TOKEN_CACHE.get(token_cache_index, None)

    def run(self, tmp=None, task_vars=None):

        changed = False

        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)
        # del tmp  # tmp no longer has any effect

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


        if token is None and bool(barn_user) and bool(barn_password) and bool(barn_host) and bool(barn_port):
            token = self._get_token_from_cache(barn_host, barn_port, barn_user, barn_password)
            if token is None:
                try:
                    r = Request().open("POST", "http://%s:%s/login" % (barn_host, barn_port),
                                       url_username=barn_user,
                                       url_password=barn_password,
                                       force_basic_auth=True)
                    if r.code != 200:
                        result['changed'] = False
                        result['failed'] = True
                        result['msg'] = "Authentication error, Can't login into barn server"
                        return result
                    token = json.loads(r.read()).get("token")
                    self._set_token_in_cache(barn_host, barn_port, barn_user, barn_password, token)
                except Exception as e:
                    result["failed"] = True
                    result["msg"] = e

        try:
            host=task_vars.get("inventory_hostname")

            data={
                "name": host
            }
            r = Request().open("POST","http://%s:%s/query"% (barn_host, barn_port),
                            data=json.dumps(data).encode('utf-8'),
                            headers={'Content-type': 'application/json', "x-access-tokens": token})
            result["vars"]=json.loads(r.read()).get("vars",{})
        except Exception as e:
            result['msg'] = e

        # host=task_vars.get("inventory_hostname")

        # data={
        #     "name": host
        # }

        result["changed"] = changed
        return result
