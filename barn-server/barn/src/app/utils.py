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


def merge_args_data(args, data=None):
    """
        Merge arg and data into one directory
    """
    output = args.copy()
    if data:
        for k, v in data.items():
            output[k] = v
    return output
