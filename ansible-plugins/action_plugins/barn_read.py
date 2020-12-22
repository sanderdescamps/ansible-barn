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

        barn_host = module_args.get("barn_host", None)
        barn_port = module_args.get("barn_port", 443)
        barn_url = module_args.get("barn_url", None)
        barn_https = ensure_type(module_args.get("barn_https", True), 'bool')
        validate_certs = module_args.get("validate_certs", True)
        barn_user = module_args.get("barn_user", None)
        barn_password = module_args.get("barn_password", None)
        token = module_args.get("barn_token", None)
        load_to_facts = module_args.get("load_to_facts", False)
        include = ensure_type(module_args.get("include", []), 'list')
        exclude = ensure_type(module_args.get("exclude", []), 'list')

        if not barn_url and barn_host and barn_port:
            protocol = "https" if barn_https else "http"
            barn_url = "{}://{}:{}".format(protocol, barn_host, barn_port)
            self._display.warning(
                "The options barn_host and barn_port are deprecated. Please use barn_url instead.")
        elif barn_url and not barn_url.startswith("https://") and not barn_url.startswith("http://"):
            protocol = "http" if "barn_https" in module_args and not barn_https else "https"
            barn_url = "{}://{}".format(protocol, barn_url)
        barn_url = barn_url.rstrip("/")

        if barn_url is None:
            result['changed'] = False
            result['failed'] = True
            result['msg'] = "barn_host is required"
            return result

        query_args = dict(
            follow_redirects=True,
            validate_certs=validate_certs
            )
        query_args["headers"] = {'Content-type': 'application/json'}
        if token:
            query_args["headers"]["x-access-tokens"] = token
        if barn_user:
            query_args["url_username"] = barn_user
            query_args["force_basic_auth"] = True
        if barn_password:
            query_args["url_password"] = barn_password
            query_args["force_basic_auth"] = True

        try:
            data = {
                "name": task_vars.get("inventory_hostname"),
                'type': "host"
            }
            query_args["data"] = json.dumps(data).encode('utf-8')
            self._display.vvv(
                "POST {}/api/v1/inventory/hosts".format(barn_url))
            r = Request().open("POST", "{}/api/v1/inventory/hosts".format(barn_url), **query_args)
            barn_resp = json.loads(r.read())
            self._display.vvv("Response form Barn: %s" % (barn_resp))
            barn_vars = barn_resp.get(
                "result", {})[0].get("vars", {})

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
                result = json.loads(e.read())
            except AttributeError:
                result["status"] = 500
                result["error"] = "Can't parse API response to json response"
                result["failed"] = True
        except timeout:
            result["status"] = 503
            result["error"] = "Connection timeout"
            result["failed"] = True
        except urllib_error.URLError as e:
            result["status"] = 503
            result["error"] = "Can't connect to barn"
            result["failed"] = True
        except Exception as e:
            raise AnsibleActionFail(e)

        return result
