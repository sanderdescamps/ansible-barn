import json
from socket import timeout
from ansible.plugins.action import ActionBase
from ansible.module_utils.urls import Request
from ansible.errors import AnsibleActionFail
from ansible.module_utils.urls import urllib_error


def list_parser(to_parse):
    """
        split a string or list of strings into seperate strings. Seperated by comma or spaces.
    """
    output = []
    if type(to_parse) is str:
        output = to_parse.replace(', ', ',').replace(' ', ',').split(',')
    elif type(to_parse) is list:
        for i in to_parse:
            output.extend(list_parser(i))
    else:
        output = str(to_parse).replace(', ', ',').replace(' ', ',').split(',')
    return list(set(output))


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
        load_to_facts = module_args.get("load_to_facts", False)
        include = list_parser(module_args.get("include", []))
        exclude = list_parser(module_args.get("exclude", []))

        if barn_host is None:
            result['changed'] = False
            result['failed'] = True
            result['msg'] = "host is required"
            return result

        try:
            data = {
                "name": task_vars.get("inventory_hostname"),
                'type': "host"
            }

            # query_args = dict(data=json.dumps(data).encode('utf-8'))
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

            r = Request().open("GET", "http://%s:%s/nodes" %
                               (barn_host, barn_port), **query_args)
            barn_vars = json.loads(r.read()).get(
                "results", {})[0].get("vars", {})

            if len(include) > 0:
                barn_vars = {i: barn_vars[i] for i in include}
            if len(exclude) > 0:
                barn_vars = {i: barn_vars[i]
                             for i in barn_vars if i not in exclude}

            result["vars"] = barn_vars
            if load_to_facts:
                result['ansible_facts'] = barn_vars
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

        result["changed"] = changed
        return result
