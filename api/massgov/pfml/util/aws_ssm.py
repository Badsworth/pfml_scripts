def get_secret(client, key):
    res = client.get_parameter(Name=key, WithDecryption=True)
    return res["Parameter"]["Value"]
