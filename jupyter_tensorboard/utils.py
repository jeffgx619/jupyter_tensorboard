def concat_params_to_str(params_dict):
    return ','.join("%s=%s" % (key,val) for (key,val) in params_dict.items())


def split_params_to_dict(params_string):
    print(params_string)
    print(type(params_string))
    dd = {}
    if isinstance(params_string, bytes) and not isinstance(params_string, str):
        params_string = str(params_string, 'utf-8')
    params = params_string.split(',')
    for entry in params:
        key_value = entry.split('=')
        dd[key_value[0]] = key_value[1]
    return dd