import base64


def encode_to_base64(string):
  encoded_string = base64.b64encode(string.encode('utf-8'))
  return encoded_string.decode('utf-8')


def generate_mapping_result(raw_data, mapping_dict: dict = None, include_label=False):
  if not include_label:
    for item in raw_data:
      yield {key: value["value"] for key, value in item.items()}
  else:
    for item in raw_data:
      final = {}
      for mapping_key, mapping_value in mapping_dict.items():
        final.update(
            {mapping_value: item[mapping_key]["value"]})
      yield final
