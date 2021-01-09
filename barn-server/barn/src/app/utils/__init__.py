import string
import random

def list_parser(to_parse):
    """
        Split a string or list of strings into seperate strings. Seperated by comma or spaces.
        (if to_parse is None, methode will return None)
    """
    output = []
    if to_parse is None:
        return None
    elif isinstance(to_parse, str):
        output = to_parse.replace(', ', ',').replace(' ', ',').split(',')
    elif isinstance(to_parse, list):
        for i in to_parse:
            output.extend(list_parser(i))
    else:
        output = list_parser(str(to_parse))
    return list(set(output))

BOOLEANS_TRUE = frozenset(('y', 'yes', 'on', '1', 'true', 't', 1, 1.0, True))
BOOLEANS_FALSE = frozenset(('n', 'no', 'off', '0', 'false', 'f', 0, 0.0, False))
BOOLEANS = BOOLEANS_TRUE.union(BOOLEANS_FALSE)

def boolean_parser(value, default_to_false=True):
    if isinstance(value, bool):
        return value

    normalized_value = value
    if isinstance(value, str):
        normalized_value = value.lower().strip()

    if normalized_value in BOOLEANS_TRUE:
        return True
    elif normalized_value in BOOLEANS_FALSE or default_to_false:
        return False

    raise TypeError("The value '%s' is not a valid boolean.  Valid booleans include: %s" % (value, ', '.join(repr(i) for i in BOOLEANS)))

def remove_empty_fields(data):
    output = None
    if isinstance(data, dict):
        output = {}
        for key,value in data.items():
            if value and (isinstance(value, dict) or isinstance(value,list)):
                output[key] = remove_empty_fields(value)
            elif bool(value):
                output[key] = value
    elif isinstance(data, list):
        output = []
        for value in data:
            if data and (isinstance(value, dict) or isinstance(value,list)):
                output.append(remove_empty_fields(value))
            elif bool(value):
                output.append(value)
    else:
        output = data
    return output

def merge_args_data(args, data=None):
    """
        Merge arg and data into one directory
    """
    output = args.copy()
    if data:
        for k, v in data.items():
            output[k] = v
    return output

def remove_underscore_keys(d):
    """
      Recursivly remove underscore keys from directory or list of directories
    """
    res = {}
    if type(d) == dict:
        for k, v in d.items():
            if k.startswith('_'):
                pass
            elif type(v) == dict or type(v) == list:
                res[k] = remove_underscore_keys(v)
            else:
                res[k] = v
    elif type(d) == list:
        res = list(map(lambda x: remove_underscore_keys(x)
                       if type(x) == dict else x, d))
    return res

def generate_password(length=32):
    char_set = f'{string.ascii_letters}{string.digits}/*-+&!$<>@=?%'
    return ''.join(random.choice(char_set) for i in range(length))
