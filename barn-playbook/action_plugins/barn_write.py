import json
from socket import timeout
from ansible.plugins.action import ActionBase
from ansible.module_utils.urls import Request
from ansible.errors import AnsibleActionFail
from ansible.module_utils.urls import urllib_error


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):

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
        state = module_args.get("state", None)
        barn_vars = module_args.get("vars", {})
        vars_to_remove = module_args.get("remove_vars",[])

        if barn_host is None:
            result['changed'] = False
            result['failed'] = True
            result['msg'] = "host is required"
            return result

        if state == 'present':
            try:
                data = {
                    "name": task_vars.get("inventory_hostname"),
                    'type': "host",
                    "vars": barn_vars,
                    "remove_vars": vars_to_remove
                }

                query_args = dict()
                query_args["data"] = json.dumps(data).encode('utf-8')
                query_args["headers"] = {'Content-type': 'application/json'}
                if token:
                    query_args["headers"]["x-access-tokens"] = token
                if barn_user:
                    query_args["url_username"] = barn_user
                    query_args["force_basic_auth"] = True
                if barn_password:
                    query_args["url_password"] = barn_password
                    query_args["force_basic_auth"] = True

                resp = Request().open("PUT", "http://%s:%s/hosts" %
                                      (barn_host, barn_port), **query_args)
                resp_json = json.loads(resp.read())

                result["changed"] = resp_json.get('changed')
                result["vars"] = resp_json.get("host", {}).get("vars", {})

            except urllib_error.HTTPError as e:
                result["status"] = int(getattr(e, 'code', -1))
                try:
                    body = json.loads(e.read())
                except AttributeError:
                    body = {}
                result["error"] = body.get("error", "")
                result['failed'] = True
            except timeout:
                result["status"] = 500
                result["error"] = "Connection timeout"
            except Exception as e:
                raise AnsibleActionFail(e)

        elif state == "absent":
            resp_json["msg"] = "remove %s from barn" % (
                task_vars.get("inventory_hostname"))

        return result
