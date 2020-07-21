from http import HTTPStatus
from mongoengine.queryset import QuerySet
from flask import jsonify, make_response
from app.models import Node, Host, Group

class ResponseFormater():
    def __init__(self):
        self._failed = False
        self._changed = False
        self._msg = []
        self._result = []
        self._status = 200
        self._header = {}
    
    def __add__(self, other):
        if isinstance(other, ResponseFormater):
            new = ResponseFormater()
            new._failed = self._failed or other._failed
            new._changed = self._changed or other._changed
            new._status = self._status if self._status >= other._status else other._status
            new._msg = list(set(self._msg + other._msg))
            new._header.update(other._header)
            new._header.update(self._header)
            new._result = list(set(self._result + other._result))
            return new
        else:
            raise TypeError


    def changed(self, changed=True):
        self._changed = changed
        return self

    def failed(self, msg=None, failed=True, changed=None, status=HTTPStatus.BAD_REQUEST):
        self._failed = failed
        self._status = status
        if msg:
            self._msg.append(msg)
        if changed is not None:
            self._changed = changed
        return self

    def succeed(self, msg=None, failed=False, changed=None, status=HTTPStatus.OK):
        self._failed = failed
        self._status = status
        if msg:
            self._msg.append(msg)
        if changed is not None:
            self._changed = changed
        return self

    def authentication_error(self, msg=None):
        return self.add_header({'WWW.Authentication': 'Basic realm="login required"'}).failed(msg=msg, failed=True, status=401)


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
                    raise TypeError("unsupported result type")
        else:
            raise TypeError("unsupported result type")

    def add_header(self, header_dict):
        self._header.update(header_dict)
        return self

    def format(self):
        return dict(changed=self._changed, failed=self._failed, msg=self._msg, result=self._result, status=self._status)

    def get_changed(self):
        """ return if a change is registered """
        return self._changed
    
    def get_response(self):
        """
            return json response object which can be used by Flask
        """
        return make_response(jsonify(self.format()), self._status, self._header)
