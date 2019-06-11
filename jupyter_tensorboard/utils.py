def concat_params_to_str(params_dict):
    return ','.join("%s=%s" % (key,val) for (key,val) in params_dict.iteritems())


def split_params_to_dict(params_string):
    dd = {}
    params = params_string.split(',')
    for entry in params:
        key_value = entry.split('=')
        dd[key_value[0]] = key_value[1]
    return dd