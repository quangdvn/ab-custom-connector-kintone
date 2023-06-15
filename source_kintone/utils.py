import base64


def encode_to_base64(string):
  encoded_string = base64.b64encode(string.encode('utf-8'))
  return encoded_string.decode('utf-8')
