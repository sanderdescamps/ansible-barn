def list_parser(to_parse):
    """
        split a string or list of strings into seperate strings. Seperated by comma or spaces.
    """
    output = []
    if isinstance(to_parse, str):
        output = to_parse.replace(', ', ',').replace(' ', ',').split(',')
    elif isinstance(to_parse, list):
        for i in to_parse:
            output.extend(list_parser(i))
    else:
        output = list_parser(str(to_parse))
    return list(set(output))
