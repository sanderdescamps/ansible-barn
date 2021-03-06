#!/usr/bin/env python3
import os
import sys
import json
import yaml
import click
from ansible.module_utils.urls import Request, urllib_error
from ansible.utils.vars import merge_hash
from ansible.config.manager import ensure_type
from urllib.error import HTTPError
from werkzeug.security import generate_password_hash


# BARN_CONFIG_PATHS = [
#     os.path.join(os.getcwd(), "barn.yml"),
#     os.path.join(os.getcwd(), "barn.yaml"),
#     os.path.join(os.getcwd(), "barn.json"),
#     os.path.join(os.path.expanduser("~"), ".barn.yml"),
#     os.path.join(os.path.expanduser("~"), ".barn.yaml"),
#     os.path.join(os.path.expanduser("~"), ".barn.json"),
#     os.path.join("/etc/barn/", "barn.yml"),
#     os.path.join("/etc/barn/", "barn.yaml"),
#     os.path.join("/etc/barn/", "barn.json")
# ]

BARN_CONFIG_PATHS = [
    [
        os.path.join(os.getcwd(), "barn.yml"),
        os.path.join(os.getcwd(), "barn.yaml"),
        os.path.join(os.getcwd(), "barn.json")
    ], [
        os.path.join(os.path.expanduser("~"), ".barn.yml"),
        os.path.join(os.path.expanduser("~"), ".barn.yaml"),
        os.path.join(os.path.expanduser("~"), ".barn.json")
    ], [
        os.path.join("/etc/barn/", "barn.yml"),
        os.path.join("/etc/barn/", "barn.yaml"),
        os.path.join("/etc/barn/", "barn.json")
    ]
]


class Barn(object):
    def __init__(self, url=None, user=None, password=None, token=None, validate_certs=True):
        self.barn_url = url
        self.barn_user = user
        self.barn_password = password
        self.barn_token = token
        self.validate_certs = validate_certs

    def request(self, method, path, headers=None, data=None):
        query_args = dict(
            follow_redirects=True,
            validate_certs=self.validate_certs
        )
        headers = headers if headers is not None else {}
        data = data if data is not None else {}
        headers.update({'Content-type': 'application/json'})
        query_args["headers"] = headers
        query_args["data"] = json.dumps(data).encode('utf-8')

        authentication="none"
        if self.barn_token:
            authentication="token"
            query_args["headers"]["x-access-tokens"] = self.barn_token
        elif self.barn_user and self.barn_password:
            authentication="userpass"
            query_args["url_username"] = self.barn_user
            query_args["url_password"] = self.barn_password
            query_args["force_basic_auth"] = True


        try:
            resp = Request().open(method.upper(), "%s/%s" %
                                  (self.barn_url, path.lstrip('/')), **query_args)
            
            result = BarnResult.from_response(resp)
            result["request"] = dict(url="%s/%s" % (self.barn_url, path.lstrip('/')), method=method,authentication=authentication)
            return result
        except (urllib_error.HTTPError, HTTPError) as e:
            try:
                result = BarnResult.from_dict(json.loads(e.read()))
                result["status"] = int(getattr(e, 'code', -1))
                result["request"] = dict(
                    url="%s/%s" % (self.barn_url, path.lstrip('/')), method=method)
                return result
            except AttributeError:
                result = BarnResult.from_dict(dict(
                    status=None,
                    failed=True,
                    changed=False
                ))
                result["request"] = dict(
                    url="%s/%s" % (self.barn_url, path.lstrip('/')), method=method)
                result.set_main_message(
                    "Can't parse API response to json response")
                return result
        return None

    def __str__(self):
        output = dict(
            barn_url=self.barn_url,
            validate_certs=self.validate_certs
        )
        if self.barn_user and self.barn_password:
            output["barn_user"] = self.barn_user
            output["barn_password"] = "*"*len(self.barn_password)
        if self.barn_token:
            output["barn_token"] = self.barn_token
        return str(output)

    @classmethod
    def from_config(cls, config):
        """
            plugin: barn
            barn_url: https://barn.example.com
            barn_user: sdescamps
            barn_password: testpassword
            #barn_hostname: 127.0.0.1
            #barn_port: 5000
            #barn_https: true
            fetch_variables: false
        """

        barn_user = config.get("barn_user", None)
        barn_password = config.get("barn_password", None)
        barn_token = config.get("barn_token", None)
        barn_url = config.get("barn_url", None)
        barn_host = config.get("barn_host", config.get("barn_hostname", None))
        barn_port = config.get("barn_port", None)
        barn_https = ensure_type(config.get("barn_https", True), 'bool')
        validate_certs = config.get("validate_certs", True)

        if not barn_url and barn_host and barn_port:
            protocol = "https" if barn_https else "http"
            barn_url = "{}://{}:{}".format(protocol, barn_host, barn_port)
        elif barn_url and not barn_url.startswith("https://") and not barn_url.startswith("http://"):
            protocol = "http" if "barn_https" in config and not barn_https else "https"
            barn_url = "{}://{}".format(protocol, barn_url)
        barn_url = barn_url.rstrip("/") if barn_url else barn_url

        return Barn(
            url=barn_url,
            user=barn_user,
            password=barn_password,
            token=barn_token,
            validate_certs=validate_certs
        )


class BarnContext(dict):
    pass


pass_barn_context = click.make_pass_decorator(BarnContext)


class BarnResult(dict):

    def set_main_message(self, message):
        """Set the main message of the response. Message will also be added to the msg_list. 

        Args:
            message (str): Message

        Returns:
            ResponseFormatter: return self
        """
        self.add_message(message)
        self["msg"] = message
        return self

    def add_message(self, message):
        """Add a message to the logs of the response

        Args:
            message (str): message

        Returns:
            ResponseFormatter: return self
        """
        if "msg_list" not in self:
            self["msg_list"] = []
        self["msg_list"].append(message)
        return self

    @classmethod
    def from_response(cls, response):
        json_response = None
        try:
            json_response = json.loads(response.read())
            if "status" not in json_response and response.status:
                json_response["status"] = response.status
            
            json_response["response"] = dict()
            if hasattr(response, "url"):
                json_response["response"]["url"] = getattr(response, "url")
            # if hasattr(response, "headers"):
            #     json_response["response"]["headers"] = dict(getattr(response, "headers"))
            # if hasattr(response, "version"):
            #     json_response["response"]["version"] = getattr(response, "version")
        except json.JSONDecodeError as _:
            json_response = dict(
                msg="Failed to format the response",
                failed=True
            )
        return BarnResult.from_dict(json_response)

    @classmethod
    def from_dict(cls, response_dict):
        result = BarnResult()
        result.update(response_dict)
        return result

    def failed(self):
        return not self.succeed()

    def succeed(self):
        status = self.get("status")
        return True if status and status >= 200 and status <= 299 else False

    def to_text(self):
        output = []
        if self.succeed():
            output.append("Status: {}".format(
                click.style("succeeded", fg='green')))
        else:
            output.append("Status: {}".format(click.style("failed", fg='red')))
        output.append("Status code: {}".format(self.get("status")))

        output.append("Changed: {}".format(
            str(self.get("changed", "unknown"))))

        msg_list = self.get("msg_list") or ([self.get("msg")] if self.get("msg", []) != [] else None) or []
        if self.get("msg_list", []) != []:
            output.append("Message:")
            for msg in msg_list:
                output.append("  {}".format(click.style(
                    msg, bold=(self.get("msg") == msg))))
        elif self.get("msg", "") != "":
            output.append("  Message: {}".format(
                click.style(self.get("msg"), bold=True)))

        if self.get("result", []) != []:
            output.append("Results: ")
            for result in self.get("result", []):
                if result.get("type", "").upper() == "USER":
                    output.append("  {}: {} ({})".format(result.get(
                        "type").upper(), result.get("username"), result.get("name")))
                else:
                    output.append("  {}: {}".format(result.get(
                        "type", "unknown").upper(), result.get("name")))
                if len(self.get("results", [])) == 1 and len(result.get("vars", [])) > 0:
                    for line in str(yaml.dump(result.get("vars", []))).split("\n"):
                        output.append("    {}".format(line))

        return "\n".join(output)

    def to_json(self, indent=2):
        return json.dumps(self, indent=indent)

    def to_yaml(self, indent=4):
        return yaml.dump(dict(self), indent=indent)


def _load_barn_config_file(path):
    barn_vars = {}
    try:
        with open(path, 'r') as file:
            barn_vars = yaml.load(file, Loader=yaml.FullLoader)
    except yaml.YAMLError as e:
        msg = getattr(e, 'problem') if hasattr(
            e, 'problem') else "unknown problem"
        click.secho("Failed to load config: {} ({})".format(
            path, msg), fg="red")
    return barn_vars


def _load_barn_system_config():
    barn_vars = {}
    for path_set in BARN_CONFIG_PATHS:
        for path in path_set:
            if os.path.exists(path):
                barn_vars = merge_hash(_load_barn_config_file(path), barn_vars)
                break
    return barn_vars


@click.group(context_settings={'help_option_names': ['-h', '--help']})
@click.option('--ask-barn-user', help='Ask for barn user', is_flag=True, default=False, show_default=True)
@click.option('--ask-barn-password', help='Ask for barn password', is_flag=True, default=False, show_default=True)
@click.option('-u', '--barn-user', '--user', help='User to authenticate against barn')
@click.option('-p', '--barn-password', '--password', help='Password to authenticate against barn')
@click.option('-h', '--barn-url', '--url', help='Barn url', show_default=True)
@click.option('-t', '--barn-token', '--token', help='Barn authentication token')
@click.option('-c', '--config-file', help='path to config file')
@click.option('--skip-auth', help='debug option to skip authentication', is_flag=True, default=False, show_default=True)
@click.pass_context
def main(ctx=None, **kwargs):
    barn_vars = {}

    barn_vars_file = {}
    if "config-file" in kwargs:
        barn_vars_file = _load_barn_config_file(kwargs.get("config-file"))

    barn_vars_system = _load_barn_system_config()
    barn_vars_env = {key: value for key,
                     value in os.environ.items() if key.startswith("BARN_")}
    barn_vars_cli = kwargs
    if kwargs.get("ask_barn_user"):
        barn_vars_cli["barn_user"] = click.prompt('Barn username', type=str)
    if kwargs.get("ask_barn_password"):
        barn_vars_cli["barn_password"] = click.prompt(
            'Barn password', hide_input=True, type=str)

    barn_user = barn_vars_cli.get("barn_user") or barn_vars_env.get(
        "BARN_USER") or barn_vars_file.get("barn_user") or barn_vars_system.get("barn_user")
    barn_password = barn_vars_cli.get("barn_password") or barn_vars_env.get(
        "BARN_PASSWORD") or barn_vars_file.get("barn_password") or barn_vars_system.get("barn_password")
    if barn_user and barn_password:
        barn_vars["barn_user"] = barn_user
        barn_vars["barn_password"] = barn_password
    
    barn_token = barn_vars_cli.get("barn_token") or barn_vars_env.get(
        "BARN_TOKEN") or barn_vars_file.get("barn_token") or barn_vars_system.get("barn_token")
    if barn_token:
        barn_vars["barn_token"] = barn_token


    if barn_vars_cli.get("barn_url"):
        barn_vars["barn_url"] = barn_vars_cli.get("barn_url")
        barn_vars["validate_certs"] = barn_vars_cli.get("validate_certs", True)
    elif barn_vars_env.get("BARN_URL"):
        barn_vars["barn_url"] = barn_vars_env.get("BARN_URL")
        barn_vars["validate_certs"] = barn_vars_env.get("BARN_VALIDATE_CERTS", True)
    elif barn_vars_file.get("barn_url"):
        barn_vars["barn_url"] = barn_vars_file.get("barn_url")
        barn_vars["validate_certs"] = barn_vars_file.get("validate_certs", True)
    elif barn_vars_system.get("barn_url"):
        barn_vars["barn_url"] = barn_vars_system.get("barn_url")
        barn_vars["validate_certs"] = barn_vars_system.get("validate_certs", True)

    if kwargs.get("skip_auth"):
        barn_vars.pop("barn_password",None)
        barn_vars.pop("barn_user",None)

    barn = Barn.from_config(barn_vars)
    ctx.obj = BarnContext(barn=barn)


@main.group()
@pass_barn_context
def get(barn_context=None, *args, **kwargs):
    pass


@main.group()
@pass_barn_context
def add(barn_context=None):
    pass


@main.group()
@pass_barn_context
def delete(barn_context=None):
    pass


@main.command(name="login")
@click.option('--format', help="Output format", type=click.Choice(['text', 'json', 'yaml']), default="text", show_default="text")
@click.option('--json', '-j', help="Same as --format=json", is_flag=True, default=False)
@click.option('--yaml', help="Same as --format=yaml", is_flag=True, default=False)
@click.argument('username', required=False)
@pass_barn_context
def login(barn_context=None, username=None, **kwargs):
    barn = barn_context.get("barn")
    barnresult = barn.request("POST", "/token")
    token = barnresult.get("token")

    if kwargs.get("format") == "json" or kwargs.get("json"):
        click.echo(barnresult.to_json())
    elif kwargs.get("format") == "yaml" or kwargs.get("yaml"):
        click.echo(barnresult.to_yaml())
    else:
        barnresult = barnresult.add_message("Run following command to store token to enviromnemt variables:")
        barnresult = barnresult.add_message("# export BARN_TOKEN={token}".format(token=token))
        click.echo(barnresult.to_text())



@get.command(name="host")
@click.option('--format', help="Output format", type=click.Choice(['text', 'json', 'yaml']), default="text", show_default="text")
@click.option('--json', '-j', help="Same as --format=json", is_flag=True, default=False)
@click.option('--yaml', help="Same as --format=yaml", is_flag=True, default=False)
@click.option('--regex', '-r', help="Name is regular expression", is_flag=True, default=False)
@click.argument('host', required=False)
@pass_barn_context
def get_host(barn_context=None, host=None, **kwargs):
    barn = barn_context.get("barn")
    data = {}
    if host:
        data["name"] = host
    if kwargs.get("regex"):
        data["regex"] = True
    barnresult = barn.request("POST", "/api/v1/inventory/hosts", data=data)
    if kwargs.get("format") == "json" or kwargs.get("json"):
        click.echo(barnresult.to_json())
    elif kwargs.get("format") == "yaml" or kwargs.get("yaml"):
        click.echo(barnresult.to_yaml())
    else:
        click.echo(barnresult.to_text())


@get.command(name="group")
@click.option('--format', help="Output format", type=click.Choice(['text', 'json', 'yaml']), default="text", show_default="text")
@click.option('--json', '-j', help="Same as --format=json", is_flag=True, default=False)
@click.option('--yaml', help="Same as --format=yaml", is_flag=True, default=False)
@click.option('--regex', '-r', help="Name is regular expression", is_flag=True, default=False)
@click.argument('group', required=False)
@pass_barn_context
def get_group(barn_context=None, group=None, **kwargs):
    barn = barn_context.get("barn")
    data = {}
    if group:
        data["name"] = group
    if kwargs.get("regex"):
        data["regex"] = True
    barnresult = barn.request("POST", "/api/v1/inventory/groups", data=data)
    if kwargs.get("format") == "json" or kwargs.get("json"):
        click.echo(barnresult.to_json())
    elif kwargs.get("format") == "yaml" or kwargs.get("yaml"):
        click.echo(barnresult.to_yaml())
    else:
        click.echo(barnresult.to_text())


@get.command(name="node")
@click.option('--format', help="Output format", type=click.Choice(['text', 'json', 'yaml']), default="text", show_default="text")
@click.option('--json', '-j', help="Same as --format=json", is_flag=True, default=False)
@click.option('--yaml', help="Same as --format=yaml", is_flag=True, default=False)
@click.option('--regex', '-r', help="Name is regular expression", is_flag=True, default=False)
@click.option('--type', '-t', help="Define type of the node", default=None, type=click.Choice(["host", "group"]))
@click.argument('node', required=False)
@pass_barn_context
def get_node(barn_context=None, node=None, **kwargs):
    barn = barn_context.get("barn")
    data = {}
    if node:
        data["name"] = node
    if kwargs.get("regex"):
        data["regex"] = True
    if kwargs.get("type"):
        data["type"] = kwargs.get("type")
    barnresult = barn.request("POST", "/api/v1/inventory/nodes", data=data)
    if kwargs.get("format") == "json" or kwargs.get("json"):
        click.echo(barnresult.to_json())
    elif kwargs.get("format") == "yaml" or kwargs.get("yaml"):
        click.echo(barnresult.to_yaml())
    else:
        click.echo(barnresult.to_text())


@add.command(name="host")
@click.option('--variables', '--var', '-a', help="Set variable", multiple=True)
@click.option('--group', '-g', help="Group where host belongs to", multiple=True)
@click.option('--group', '-g', help="Group where host belongs to", multiple=True)
@click.option('--format', help="Output format", type=click.Choice(['text', 'json', 'yaml']), default="text", show_default="text")
@click.option('--json', '-j', help="Same as format=json", is_flag=True, default=False)
@click.option('--yaml', help="Same as format=yaml", is_flag=True, default=False)
@click.argument('name', required=True)
@pass_barn_context
def add_host(barn_context=None, name=None, **kwargs):
    """
    name: Name of the host
    """
    barn = barn_context.get("barn")
    data = dict(vars={})
    if name:
        data["name"] = name
    for variable in kwargs.get("variables", []):
        key, value = variable.split("=")
        data["vars"][key.strip()] = value.strip().strip('"').strip("'")

    barnresult = barn.request("PUT", "/api/v1/inventory/hosts/add", data=data)
    # if kwargs.get("format") == "json" or kwargs.get("json"):
    #     click.echo(json.dumps(results, indent=2))
    # elif kwargs.get("format") == "yaml" or kwargs.get("yaml"):
    #     click.echo(yaml.dump(results, indent=2))
    # else:
    #     if results.get("failed"):
    #         for msg in results.get("msg"):
    #             click.echo("Failed: %s" % (msg))
    #     else:
    #         for result in results.get("result", []):
    #             click.echo(result.get("name"))
    if kwargs.get("format") == "json" or kwargs.get("json"):
        click.echo(barnresult.to_json())
    elif kwargs.get("format") == "yaml" or kwargs.get("yaml"):
        click.echo(barnresult.to_yaml())
    else:
        click.echo(barnresult.to_text())


@delete.command(name="host")
@click.option('--format', help="Output format", type=click.Choice(['text', 'json', 'yaml']), default="text", show_default="text")
@click.option('--json', '-j', help="Same as format=json", is_flag=True, default=False)
@click.option('--yaml', help="Same as format=yaml", is_flag=True, default=False)
@click.argument('name', required=True)
@pass_barn_context
def delete_host(barn_context=None, name=None, **kwargs):
    """
    name: Name of the host
    """
    barn = barn_context.get("barn")
    data = dict(name=name)
    barnresult = barn.request("DELETE", "/api/v1/inventory/hosts", data=data)
    # if kwargs.get("format") == "json" or kwargs.get("json"):
    #     click.echo(json.dumps(results, indent=2))
    # elif kwargs.get("format") == "yaml" or kwargs.get("yaml"):
    #     click.echo(yaml.dump(results, indent=2))
    # else:
    #     if results.get("failed"):
    #         for msg in results.get("msg"):
    #             click.echo("Failed: %s" % (msg))
    #     else:
    #         for result in results.get("result", []):
    #             click.echo(result.get("name"))
    if kwargs.get("format") == "json" or kwargs.get("json"):
        click.echo(barnresult.to_json())
    elif kwargs.get("format") == "yaml" or kwargs.get("yaml"):
        click.echo(barnresult.to_yaml())
    else:
        click.echo(barnresult.to_text())


@delete.command(name="group")
@click.option('--format', help="Output format", type=click.Choice(['text', 'json', 'yaml']), default="text", show_default="text")
@click.option('--json', '-j', help="Same as format=json", is_flag=True, default=False)
@click.option('--yaml', help="Same as format=yaml", is_flag=True, default=False)
@click.argument('name', required=True)
@pass_barn_context
def delete_group(barn_context=None, name=None, **kwargs):
    """
    name: Name of the host
    """
    barn = barn_context.get("barn")
    data = dict(name=name)
    barnresult = barn.request("DELETE", "/api/v1/inventory/groups", data=data)
    if kwargs.get("format") == "json" or kwargs.get("json"):
        click.echo(barnresult.to_json())
    elif kwargs.get("format") == "yaml" or kwargs.get("yaml"):
        click.echo(barnresult.to_yaml())
    else:
        click.echo(barnresult.to_text())


@main.command(name="test", context_settings=dict(ignore_unknown_options=True))
@pass_barn_context
def test(barn_context=None, **kwargs):
    print("kwargs: {}".format(kwargs))
    print("barn: {}".format(barn_context.get("barn")))


@main.command()
@click.option('-f', '--force', help="Don't ask for confirmation", is_flag=True, default=False)
@pass_barn_context
def flush(barn_context=None, **kwargs):
    barn = barn_context.get("barn")
    confirmed = kwargs.get("force", False)
    if not confirmed:
        confirmed = click.confirm('Are you sure you want to clean barn?')
    if confirmed:
        barn.request("DELETE", "/flush")


@main.command()
@click.option('-f', '--force', help="Don't ask for confirmation", is_flag=True, default=False)
@pass_barn_context
def init(barn_context=None, **kwargs):
    barn = barn_context.get("barn")
    confirmed = kwargs.get("force", False)
    if not confirmed:
        confirmed = click.confirm('Are you sure you want to initialize barn?')
    if confirmed:
        barn.request("PUT", "/init")


@add.command(name="user")
@click.option('--format', help="Output format", type=click.Choice(['text', 'json', 'yaml']), default="text", show_default="text")
@click.option('--json', '-j', help="Same as format=json", is_flag=True, default=False)
@click.option('--yaml', help="Same as format=yaml", is_flag=True, default=False)
@click.argument('username', default=None, required=False)
@click.option('--name', '-n', help="Full name of the user")
@click.option('--role', '-r', help="User role", multiple=True)
@click.option('--password', '-p', help="User password")
@click.option('--wizard', '-w', help="Launch user wizard in cli", is_flag=True, default=False)
@pass_barn_context
def add_user(barn_context=None, username=None, **kwargs):
    allowed_user_args = ["name", "active", "password", "password_hash"]
    data = {key: value for key, value in kwargs.items(
    ) if key in allowed_user_args and value}
    if username:
        data["username"] = username

    if kwargs.get("wizard", False) or not username:
        click.echo("User wizard")
        if not data.get("username"):
            data["username"] = click.prompt(
                '  Username', type=str, default=None)
        if not data.get("name"):
            data["name"] = click.prompt(
                '  Name', type=str, default="", show_default=False)
        if not kwargs.get("role"):
            data["roles"] = []
            while(True):
                role = click.prompt('  Role {}'.format(
                    len(data["roles"])+1), type=str, default="", show_default=False)
                if role != "":
                    data["roles"].append(role.replace(" ", ""))
                else:
                    break
        if not data.get("password") and not data.get("password_hash"):
            while(True):
                password = click.prompt(
                    '  Password', hide_input=True, type=str)
                if password == click.prompt('  Repeat password', hide_input=True, type=str):
                    data["password_hash"] = generate_password_hash(
                        password, method='sha256')
                    break
                else:
                    click.secho("   Sorry, passwords do not match.", fg='red')

    barn = barn_context.get("barn")
    barnresult = barn.request("PUT", "/api/v1/admin/users/add", data=data)
    if kwargs.get("format") == "json" or kwargs.get("json"):
        click.echo(barnresult.to_json())
    elif kwargs.get("format") == "yaml" or kwargs.get("yaml"):
        click.echo(barnresult.to_yaml())
    else:
        click.echo(barnresult.to_text())


@get.command(name="user")
@click.option('--format', help="Output format", type=click.Choice(['text', 'json', 'yaml']), default="text", show_default="text")
@click.option('--json', '-j', help="Same as format=json", is_flag=True, default=False)
@click.option('--yaml', help="Same as format=yaml", is_flag=True, default=False)
@click.argument('username', default=None, required=False)
@click.option('--name', '-n', help="Full name of the user")
@click.option('--role', '-r', help="User role", multiple=True)
@click.option('--wizard', '-w', help="Launch user wizard in cli", is_flag=True, default=False)
@pass_barn_context
def get_user(barn_context=None, username=None, **kwargs):
    data = dict()
    if username:
        data["username"] = username
    if kwargs.get("name"):
        data["name"] = username or kwargs.get("name")
    barn = barn_context.get("barn")
    barnresult = barn.request("POST", "/api/v1/admin/users", data=data)
    if kwargs.get("format") == "json" or kwargs.get("json"):
        click.echo(barnresult.to_json())
    elif kwargs.get("format") == "yaml" or kwargs.get("yaml"):
        click.echo(barnresult.to_yaml())
    else:
        click.echo(barnresult.to_text())


if __name__ == '__main__':
    main()
