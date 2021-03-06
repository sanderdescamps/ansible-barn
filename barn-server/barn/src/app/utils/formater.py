from http import HTTPStatus
from mongoengine.queryset import QuerySet
from flask import jsonify, make_response
from app.models import Node, Host, Group, User


class ResponseFormater():
    def __init__(self):
        self._failed = False
        self._changed = False
        self._msg = ""
        self._msg_list = []
        self._result = []
        self._status = 200
        self._header = {}

    def __add__(self, other):
        if isinstance(other, ResponseFormater):
            new = ResponseFormater()
            new._failed = self._failed or other._failed
            new._changed = self._changed or other._changed
            new._status = self._status if self._status >= other._status else other._status
            new._msg = self._msg if other._msg is None or other._msg == "" else other._msg
            new._msg_list = list(self._msg_list + other._msg_list)
            new._header.update(other._header)
            new._header.update(self._header)
            new._result = list(set(self._result + other._result))
            return new
        else:
            raise TypeError

    def changed(self, changed=True):
        """Register a change in the response

        Args:
            changed (bool, optional): Response changed status. Defaults to True.

        Returns:
            ResponseFormatter: return self
        """
        self._changed = changed
        return self

    def failed(self, msg=None, failed=True, changed=None, status=HTTPStatus.BAD_REQUEST):
        """Register a failure

        Args:
            msg (str, optional): Set a main message. Defaults to None.
            failed (bool, optional): Set failed status. Defaults to True.
            changed (bool, optional): Set changed status. Defaults to None.
            status (int, optional): Set Status code. Defaults to HTTPStatus.BAD_REQUEST.

        Returns:
            ResponseFormatter: return self
        """
        self._failed = failed
        self._status = status
        if msg:
            self.set_main_message(msg)
        if changed is not None:
            self._changed = changed
        return self

    def succeed(self, msg=None, failed=False, changed=None, status=HTTPStatus.OK):
        """Register a successful operation. 

        Args:
            msg (str, optional): Set a main message. Defaults to None.
            failed (bool, optional): Set failed status. Defaults to True.
            changed (bool, optional): Set changed status. Defaults to None.
            status (int, optional): [description]. Defaults to HTTPStatus.OK.

        Returns:
            ResponseFormatter: return self
        """
        self._failed = failed
        self._status = status
        if msg:
            self.set_main_message(msg)
        if changed is not None:
            self._changed = changed
        return self

    def authentication_error(self, msg=None):
        """Register a authentication error

        Args:
            msg (str, optional): Set a main message. Defaults to None.

        Returns:
            ResponseFormatter: return self
        """
        return self.add_header({
            'WWW.Authentication': 'Basic realm="login required"'
        }).failed(msg=msg, failed=True, status=401)

    def set_main_message(self, message):
        """Set the main message of the response. Message will also be added to the msg_list. 

        Args:
            message (str): Message

        Returns:
            ResponseFormatter: return self
        """
        self._msg_list.append(message)
        self._msg = message
        return self

    def add_message(self, message):
        """Add a message to the logs of the response

        Args:
            message (str): message

        Returns:
            ResponseFormatter: return self
        """
        self._msg_list.append(message)
        self._msg = message
        return self

    def add_result(self, result):
        if isinstance(result, (dict, Host, Group, Node, User)):
            result = [result]
        if isinstance(result, QuerySet):
            result = list(result)
        if isinstance(result, list):
            for res in result:
                if isinstance(res, dict):
                    self._result.append(res)
                elif isinstance(res, Node) or isinstance(res, Host) or isinstance(res, Group) or isinstance(res, User):
                    self._result.append(res.to_barn_dict())
                else:
                    raise TypeError("unsupported result type")
        else:
            raise TypeError("unsupported result type")

    def add_header(self, header_dict):
        self._header.update(header_dict)
        return self

    def format(self):
        return dict(
            status=self._status,
            changed=self._changed,
            failed=self._failed,
            msg=self._msg_list[-1] if self._msg is None else self._msg,
            msg_list=self._msg_list,
            result=self._result
        )

    def get_changed(self):
        """ return if a change is registered """
        return self._changed

    def get_response(self):
        """
            return json response object which can be used by Flask
        """
        return make_response(jsonify(self.format()), self._status, self._header)
