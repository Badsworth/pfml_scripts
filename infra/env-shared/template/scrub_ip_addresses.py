# handler to anonymize ip addresses
import base64
import json

def does_not_contain_ip(header):
  return header['name'] != 'X-Forwarded-For'

def handler(event, context):
  transformed = []
  for record in event["records"]:
    # decode the logging data and transform it into a JSON string that we can alter
    payload=json.loads(base64.b64decode(record["data"]))
    payload['httpRequest']['headers'] = list(filter(
      does_not_contain_ip, 
      payload['httpRequest']['headers']
    ))
    # replace ip address with placeholder text
    payload['httpRequest']['clientIp'] = payload['httpRequest']['clientIp'].replace(payload['httpRequest']['clientIp'], '************')
    data_record = {
      'recordId': record['recordId'],
      'result': 'Ok',
      'data': base64.b64encode(bytes(json.dumps(payload), 'utf-8'))
    }
    transformed.append(data_record)

  return transformed
