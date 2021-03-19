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

def remove_empty_fields(data, recursive=True):
    output = None
    if isinstance(data, dict):
        output = {}
        for key,value in data.items():
            if (value and (isinstance(value, dict) or isinstance(value,list))) and recursive:
                output[key] = remove_empty_fields(value, recursive=recursive)
            elif bool(value) and bool(key):
                output[key] = value
    elif isinstance(data, list):
        output = []
        for value in data:
            if (value and (isinstance(value, dict) or isinstance(value,list))) and recursive:
                output.append(remove_empty_fields(value, recursive=recursive))
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

# def merge_collection(x, y, recursive=True, dict_merge='update' ,list_merge='replace'):
#     """
#     Return a new dictionary result of the merges of y into x,
#     so that keys from y take precedence over keys from x.
#     (x and y aren't modified)
#     """
#     if list_merge not in ('replace', 'keep', 'append', 'prepend', 'append_rp', 'prepend_rp'):
#         raise ValueError("merge_collection: 'list_merge' argument can only be equal to 'replace', 'keep', 'append', 'prepend', 'append_rp' or 'prepend_rp'")

#     if type(x) != type(y):
#         raise ValueError("merge_collection: 'x' and 'y' need to have the same type")

#     # to speed things up: if x is empty or equal to y, return y
#     # (this `if` can be remove without impact on the function
#     #  except performance)
#     if x == {} or x == y:
#         return y.copy()

#     # in the following we will copy elements from y to x, but
#     # we don't want to modify x, so we create a copy of it
#     x = x.copy()
#     y = y.copy()


#     if isinstance(x, dict): 
#         #improve performance
#         if not recursive and list_merge == 'replace':
#             x.update(y)
#             return x
#         for key, y_value in y.items():
#             if key not in x:
#                 x[key] = y_value
#                 continue
#             else : 
#                 x_value = x[key]
            
#             if isinstance(x_value, dict) and isinstance(y_value, dict):
#                 if recursive:
#                     x[key] = merge_collection(x_value,y_value,recursive,list_merge)
#                 else:
#                     x[key] = y_value
#             elif isinstance(x_value, list) and isinstance(y_value, list):
#                 if list_merge == 'replace':
#                     # replace x value by y's one as it has higher priority
#                     x[key] = y_value
#                 elif list_merge == 'append':
#                     x[key] = x_value + y_value
#                 elif list_merge == 'prepend':
#                     x[key] = y_value + x_value
#                 elif list_merge == 'append_rp':
#                     # append all elements from y_value (high prio) to x_value (low prio)
#                     # and remove x_value elements that are also in y_value
#                     # we don't remove elements from x_value nor y_value that were already in double
#                     # (we assume that there is a reason if there where such double elements)
#                     # _rp stands for "remove present"
#                     x[key] = [z for z in x_value if z not in y_value] + y_value
#                 elif list_merge == 'prepend_rp':
#                     # same as 'append_rp' but y_value elements are prepend
#                     x[key] = y_value + [z for z in x_value if z not in y_value]
#                 # else 'keep'
#                 #   keep x value even if y it's of higher priority
#                 #   it's done by not changing x[key]

#     for key, y_value in y.items():
#         # if `key` isn't in x
#         # update x and move on to the next element of y
#         if key not in x:
#             x[key] = y_value
#             continue
#         # from this point we know `key` is in x

#         x_value = x[key]

#         # if both x's element and y's element are dicts
#         # recursively "combine" them or override x's with y's element
#         # depending on the `recursive` argument
#         # and move on to the next element of y
#         if isinstance(x_value, MutableMapping) and isinstance(y_value, MutableMapping):
#             if recursive:
#                 x[key] = merge_hash(x_value, y_value, recursive, list_merge)
#             else:
#                 x[key] = y_value
#             continue

#         # if both x's element and y's element are lists
#         # "merge" them depending on the `list_merge` argument
#         # and move on to the next element of y
#         if isinstance(x_value, MutableSequence) and isinstance(y_value, MutableSequence):
#             if list_merge == 'replace':
#                 # replace x value by y's one as it has higher priority
#                 x[key] = y_value
#             elif list_merge == 'append':
#                 x[key] = x_value + y_value
#             elif list_merge == 'prepend':
#                 x[key] = y_value + x_value
#             elif list_merge == 'append_rp':
#                 # append all elements from y_value (high prio) to x_value (low prio)
#                 # and remove x_value elements that are also in y_value
#                 # we don't remove elements from x_value nor y_value that were already in double
#                 # (we assume that there is a reason if there where such double elements)
#                 # _rp stands for "remove present"
#                 x[key] = [z for z in x_value if z not in y_value] + y_value
#             elif list_merge == 'prepend_rp':
#                 # same as 'append_rp' but y_value elements are prepend
#                 x[key] = y_value + [z for z in x_value if z not in y_value]
#             # else 'keep'
#             #   keep x value even if y it's of higher priority
#             #   it's done by not changing x[key]
#             continue

#         # else just override x's element with y's one
#         x[key] = y_value

#     return x


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
