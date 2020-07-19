from app.models import Node, Host, Group
from mongoengine.queryset import QuerySet



class ResponseFormater():
    def __init__(self):
        self._failed = False
        self._changed = False
        self._msg = []
        self._result = []
        self._status = 200

    def changed(self, changed=True):
        self._changed = changed

    def failed(self, failed=True, msg=None, changed=None):
        self._failed = failed
        self._status = 400
        if msg:
            self._msg.append(msg)
        if changed is not None:
            self._changed = changed

    def authentication_error(self, msg=None):
        self._failed = True
        self._status = 401
        if msg:
            self._msg.append(msg)

    def add_result(self, result):
        if isinstance(result, (dict, Host, Group, Node)):
            result = [result]
        if isinstance(result, QuerySet):
            result = list(result)
        if isinstance(result, list):
            for res in result:
                if isinstance(res, dict):
                    self._result.append(res)
                elif isinstance(res, Node) or isinstance(res, Host) or isinstance(res, Group):
                    self._result.append(res.to_barn_dict())
                else:
                    raise TypeError("unsuported result type")
        else:
            raise TypeError("unsuported result type")

    def format(self):
        return self._result
