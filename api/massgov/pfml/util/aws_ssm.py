def get_secret(client, key):
    res = client.get_parameter(Name=key, WithDecryption=True)
    return res["Parameter"]["Value"]


def put_secret(client, key, value, overwrite=True, type="SecureString", data_type="text"):
    client.put_parameter(Name=key, Value=value, Type=type, Overwrite=overwrite, DataType=data_type)
