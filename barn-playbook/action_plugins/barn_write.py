import json
from socket import timeout
from ansible.plugins.action import ActionBase
from ansible.module_utils.urls import Request
from ansible.errors import AnsibleActionFail
from ansible.module_utils.urls import urllib_error
from ansible.config.manager import ensure_type


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


        if barn_host is None:
            result['changed'] = False
            result['failed'] = True
            result['msg'] = "host is required"
            return result

        if state == 'present':
            try:
                data = {
                    "name": task_vars.get("inventory_hostname")
                }
                if module_args.get("vars", None):
                    data["vars"] = module_args.get("vars")
                if module_args.get("remove_vars", None):
                    data["vars_absent"] = module_args.get("remove_vars")
                if module_args.get("groups", None):
                    data["groups"] = ensure_type(module_args.get("groups"), 'list')
                if module_args.get("groups_present", None):
                    data["groups_present"] = ensure_type(module_args.get("groups_present"), 'list')
                if module_args.get("groups_absent", None):
                    data["groups_absent"] = ensure_type(module_args.get("groups_absent"), 'list')
                if module_args.get("groups_set", None):
                    if not any(k in module_args for k in ("groups", "groups_present", "groups_absent")):
                        data["groups_set"] = ensure_type(module_args.get("groups_set"), 'list')
                    else:
                        self._display.warning("groups_set can't be used in combination with groups, groups_present and groups_absent. 'groups_set' will be ignored.")

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
                result = json.loads(resp.read())

            except urllib_error.HTTPError as e:
                result["status"] = int(getattr(e, 'code', -1))
                try:
                    result = json.loads(e.read())
                except AttributeError:
                    result["status"] = 500
                    result["error"] = "Can't parse API response to json response"
            except timeout:
                result["status"] = 500
                result["error"] = "Connection timeout"
            except Exception as e:
                raise AnsibleActionFail(e)

        elif state == "absent":
            result["msg"] = "remove %s from barn (under construction)" % (
                task_vars.get("inventory_hostname"))

        return result
